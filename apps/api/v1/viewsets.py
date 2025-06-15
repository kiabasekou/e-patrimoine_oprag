# apps/api/v1/viewsets.py
"""
ViewSets API optimisés avec filtres avancés, permissions granulaires et cache.
"""
from django.db.models import Q, Count, Sum, Avg, F, Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters import rest_framework as django_filters
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import pandas as pd
import xlsxwriter
from io import BytesIO
from datetime import datetime, timedelta

from apps.patrimoine.models import (
    Bien, Categorie, SousCategorie, Entite, 
    HistoriqueValeur, ResponsableBien, BienResponsabilite,
    Province, Departement, Commune
)
from .serializers import (
    BienSerializer, BienDetailSerializer, BienCreateSerializer,
    CategorieSerializer, SousCategorieSerializer,
    EntiteSerializer, EntiteDetailSerializer,
    HistoriqueValeurSerializer, ResponsabiliteSerializer,
    StatistiquesSerializer, DashboardSerializer
)
from .filters import BienFilter, EntiteFilter
from .permissions import IsOwnerOrReadOnly, CanManageBien


class OptimizedPagination(PageNumberPagination):
    """Pagination optimisée avec métadonnées enrichies."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_count': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'results': data
        })


class BienViewSet(viewsets.ModelViewSet):
    """
    ViewSet complet pour la gestion des biens avec fonctionnalités avancées.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    pagination_class = OptimizedPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = BienFilter
    search_fields = [
        'nom', 'code_patrimoine', 'description', 
        'numero_serie', 'tags', 'marque', 'modele'
    ]
    ordering_fields = [
        'nom', 'date_acquisition', 'valeur_acquisition',
        'created', 'modified', 'statut', 'etat_physique'
    ]
    ordering = ['-created']
    
    def get_queryset(self):
        """Queryset optimisé avec prefetch et select_related."""
        queryset = Bien.objects.select_related(
            'categorie',
            'sous_categorie', 
            'entite',
            'entite__commune',
            'entite__commune__departement',
            'entite__commune__departement__province',
            'created_by',
            'modified_by'
        ).prefetch_related(
            'historique_valeurs',
            'responsabilites__responsable__user',
            Prefetch(
                'responsabilites',
                queryset=BienResponsabilite.objects.filter(
                    actif=True,
                    date_fin__isnull=True
                ).select_related('responsable__user'),
                to_attr='responsabilites_actives'
            )
        ).annotate(
            nombre_historiques=Count('historique_valeurs'),
            valeur_moyenne_historique=Avg('historique_valeurs__valeur')
        )
        
        # Filtrer par entité si l'utilisateur n'est pas superadmin
        if not self.request.user.is_superuser:
            user_entites = self.request.user.responsabilite_biens.entite_principale
            if user_entites:
                queryset = queryset.filter(
                    Q(entite=user_entites) | 
                    Q(entite__parent=user_entites)
                )
        
        return queryset.filter(is_removed=False)
    
    def get_serializer_class(self):
        """Sérialiseur adapté selon l'action."""
        if self.action == 'create':
            return BienCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return BienDetailSerializer
        return BienSerializer
    
    @extend_schema(
        summary="Statistiques globales des biens",
        responses={200: StatistiquesSerializer}
    )
    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 15))  # Cache 15 minutes
    def statistiques(self, request):
        """Retourne les statistiques globales des biens."""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total_biens': queryset.count(),
            'valeur_totale': queryset.aggregate(
                total=Sum('valeur_acquisition')
            )['total'] or 0,
            'valeur_actuelle_totale': queryset.aggregate(
                total=Sum('valeur_actuelle_cache')
            )['total'] or 0,
            'repartition_statut': list(
                queryset.values('statut').annotate(
                    count=Count('id'),
                    valeur=Sum('valeur_acquisition')
                ).order_by('-count')
            ),
            'repartition_categorie': list(
                queryset.values(
                    'categorie__nom',
                    'categorie__type'
                ).annotate(
                    count=Count('id'),
                    valeur=Sum('valeur_acquisition')
                ).order_by('-valeur')
            ),
            'repartition_entite': list(
                queryset.values(
                    'entite__nom',
                    'entite__code'
                ).annotate(
                    count=Count('id'),
                    valeur=Sum('valeur_acquisition')
                ).order_by('-valeur')[:10]
            ),
            'acquisitions_par_mois': list(
                queryset.filter(
                    date_acquisition__gte=datetime.now().date() - timedelta(days=365)
                ).values(
                    mois=F('date_acquisition__month'),
                    annee=F('date_acquisition__year')
                ).annotate(
                    count=Count('id'),
                    valeur=Sum('valeur_acquisition')
                ).order_by('annee', 'mois')
            ),
            'top_10_valeur': list(
                queryset.order_by('-valeur_acquisition')[:10].values(
                    'code_patrimoine',
                    'nom',
                    'valeur_acquisition',
                    'categorie__nom'
                )
            ),
            'biens_critiques': {
                'a_reformer': queryset.filter(
                    etat_physique__in=['MAUVAIS', 'HORS_USAGE']
                ).count(),
                'sans_responsable': queryset.filter(
                    responsabilites__isnull=True
                ).count(),
                'garantie_expiree': queryset.filter(
                    date_fin_garantie__lt=datetime.now().date()
                ).count(),
                'maintenance_en_retard': queryset.filter(
                    prochaine_maintenance__lt=datetime.now().date()
                ).count(),
            }
        }
        
        serializer = StatistiquesSerializer(stats)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Export Excel des biens",
        parameters=[
            OpenApiParameter(
                name='format',
                type=OpenApiTypes.STR,
                enum=['xlsx', 'csv'],
                default='xlsx'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export des biens en Excel/CSV avec filtres appliqués."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Limiter à 10000 lignes pour éviter les timeouts
        queryset = queryset[:10000]
        
        # Préparer les données
        data = []
        for bien in queryset:
            responsable = bien.responsable_actuel
            data.append({
                'Code Patrimoine': bien.code_patrimoine,
                'Nom': bien.nom,
                'Catégorie': bien.categorie.nom,
                'Sous-catégorie': bien.sous_categorie.nom,
                'Entité': bien.entite.nom,
                'Localisation': f"{bien.commune.nom if bien.commune else ''} {bien.localisation_precise}",
                'Valeur Acquisition': float(bien.valeur_acquisition),
                'Date Acquisition': bien.date_acquisition.strftime('%d/%m/%Y'),
                'Statut': bien.get_statut_display(),
                'État': bien.get_etat_physique_display(),
                'Responsable': responsable.responsable.user.get_full_name() if responsable else '',
                'Marque': bien.marque,
                'Modèle': bien.modele,
                'N° Série': bien.numero_serie,
                'Fournisseur': bien.fournisseur,
                'Garantie': bien.date_fin_garantie.strftime('%d/%m/%Y') if bien.date_fin_garantie else '',
                'Tags': ', '.join(bien.tags) if bien.tags else '',
            })
        
        df = pd.DataFrame(data)
        
        # Générer le fichier
        output = BytesIO()
        format_type = request.query_params.get('format', 'xlsx')
        
        if format_type == 'csv':
            df.to_csv(output, index=False, encoding='utf-8-sig')
            content_type = 'text/csv'
            filename = f'export_biens_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        else:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Biens', index=False)
                
                # Formater l'Excel
                workbook = writer.book
                worksheet = writer.sheets['Biens']
                
                # Format pour les en-têtes
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#1E88E5',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Format pour les montants
                money_format = workbook.add_format({
                    'num_format': '#,##0.00 "XAF"',
                    'border': 1
                })
                
                # Appliquer les formats
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                worksheet.set_column('G:G', 15, money_format)  # Colonne valeur
                worksheet.set_column('A:A', 20)  # Code patrimoine
                worksheet.set_column('B:B', 30)  # Nom
                
                # Ajouter les filtres
                worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
                
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'export_biens_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    @extend_schema(
        summary="Import en masse de biens",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                    'mode': {'type': 'string', 'enum': ['create', 'update', 'upsert']}
                }
            }
        }
    )
    @action(
        detail=False, 
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser]
    )
    def import_bulk(self, request):
        """Import en masse de biens depuis Excel/CSV."""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'Aucun fichier fourni'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        mode = request.data.get('mode', 'create')
        
        try:
            # Lire le fichier
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                df = pd.read_excel(file)
            
            results = {
                'success': 0,
                'errors': 0,
                'details': []
            }
            
            # Traiter chaque ligne
            for index, row in df.iterrows():
                try:
                    # Mapper les données
                    data = {
                        'code_patrimoine': row.get('Code Patrimoine'),
                        'nom': row.get('Nom'),
                        'description': row.get('Description', ''),
                        'valeur_acquisition': row.get('Valeur Acquisition'),
                        'date_acquisition': pd.to_datetime(row.get('Date Acquisition')).date(),
                        # ... mapper autres champs
                    }
                    
                    if mode == 'update':
                        bien = Bien.objects.get(code_patrimoine=data['code_patrimoine'])
                        serializer = BienCreateSerializer(
                            bien, 
                            data=data, 
                            partial=True,
                            context={'request': request}
                        )
                    elif mode == 'upsert':
                        bien = Bien.objects.filter(
                            code_patrimoine=data['code_patrimoine']
                        ).first()
                        if bien:
                            serializer = BienCreateSerializer(
                                bien,
                                data=data,
                                partial=True,
                                context={'request': request}
                            )
                        else:
                            serializer = BienCreateSerializer(
                                data=data,
                                context={'request': request}
                            )
                    else:  # create
                        serializer = BienCreateSerializer(
                            data=data,
                            context={'request': request}
                        )
                    
                    if serializer.is_valid():
                        serializer.save()
                        results['success'] += 1
                    else:
                        results['errors'] += 1
                        results['details'].append({
                            'row': index + 2,
                            'errors': serializer.errors
                        })
                
                except Exception as e:
                    results['errors'] += 1
                    results['details'].append({
                        'row': index + 2,
                        'errors': str(e)
                    })
            
            return Response(results)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la lecture du fichier: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(summary="Transférer un bien vers une autre entité")
    @action(detail=True, methods=['post'])
    def transferer(self, request, pk=None):
        """Transfère un bien vers une autre entité."""
        bien = self.get_object()
        
        serializer = TransfertSerializer(data=request.data)
        if serializer.is_valid():
            nouvelle_entite = serializer.validated_data['nouvelle_entite']
            motif = serializer.validated_data.get('motif', '')
            
            # Vérifier les permissions
            if not request.user.has_perm('patrimoine.can_transfer_bien'):
                return Response(
                    {'error': 'Permission refusée'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Créer l'historique de mouvement
            mouvement = MouvementBien.objects.create(
                bien=bien,
                entite_origine=bien.entite,
                entite_destination=nouvelle_entite,
                type_mouvement='TRANSFERT',
                motif=motif,
                created_by=request.user
            )
            
            # Mettre à jour le bien
            bien.entite = nouvelle_entite
            bien.save()
            
            # Notifier les responsables
            from apps.notifications.services import NotificationService
            NotificationService.notifier_transfert_bien(bien, mouvement)
            
            return Response({
                'message': 'Bien transféré avec succès',
                'mouvement_id': str(mouvement.id)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(summary="Planifier une maintenance")
    @action(detail=True, methods=['post'])
    def planifier_maintenance(self, request, pk=None):
        """Planifie une maintenance pour le bien."""
        bien = self.get_object()
        
        serializer = MaintenanceSerializer(data=request.data)
        if serializer.is_valid():
            maintenance = serializer.save(
                bien=bien,
                created_by=request.user
            )
            
            # Mettre à jour le bien
            bien.prochaine_maintenance = maintenance.date_prevue
            bien.save()
            
            # Créer une tâche Celery pour rappel
            from apps.patrimoine.tasks import rappel_maintenance
            rappel_maintenance.apply_async(
                args=[str(maintenance.id)],
                eta=maintenance.date_prevue - timedelta(days=7)
            )
            
            return Response(
                MaintenanceSerializer(maintenance).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(summary="Générer un QR code pour le bien")
    @action(detail=True, methods=['get'])
    def qr_code(self, request, pk=None):
        """Génère un QR code pour le bien."""
        bien = self.get_object()
        
        import qrcode
        from django.conf import settings
        
        # Données du QR code
        qr_data = {
            'type': 'BIEN_OPRAG',
            'id': str(bien.id),
            'code': bien.code_patrimoine,
            'url': f"{settings.FRONTEND_URL}/biens/{bien.id}"
        }
        
        # Générer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Retourner l'image
        response = HttpResponse(content_type='image/png')
        img.save(response, 'PNG')
        return response


class EntiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des entités avec hiérarchie.
    """
    queryset = Entite.objects.select_related(
        'parent',
        'responsable',
        'commune__departement__province'
    ).prefetch_related(
        'sous_entites',
        'biens'
    ).annotate(
        nombre_biens=Count('biens'),
        valeur_totale_biens=Sum('biens__valeur_acquisition'),
        nombre_sous_entites=Count('sous_entites')
    )
    serializer_class = EntiteSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = EntiteFilter
    search_fields = ['nom', 'code', 'responsable__first_name', 'responsable__last_name']
    ordering_fields = ['nom', 'created', 'type']
    ordering = ['type', 'nom']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EntiteDetailSerializer
        return EntiteSerializer
    
    @extend_schema(summary="Arbre hiérarchique des entités")
    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 30))  # Cache 30 minutes
    def arbre(self, request):
        """Retourne l'arbre hiérarchique complet des entités."""
        
        def build_tree(parent=None):
            entites = Entite.objects.filter(
                parent=parent,
                actif=True
            ).order_by('type', 'nom')
            
            tree = []
            for entite in entites:
                node = {
                    'id': str(entite.id),
                    'nom': entite.nom,
                    'code': entite.code,
                    'type': entite.type,
                    'responsable': entite.responsable.get_full_name() if entite.responsable else None,
                    'nombre_biens': entite.biens.count(),
                    'enfants': build_tree(entite)
                }
                tree.append(node)
            
            return tree
        
        return Response(build_tree())
    
    @extend_schema(summary="Dashboard de l'entité")
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Retourne le dashboard complet d'une entité."""
        entite = self.get_object()
        
        # Inclure les sous-entités
        entites_ids = [entite.id]
        entites_ids.extend(
            entite.sous_entites.values_list('id', flat=True)
        )
        
        biens = Bien.objects.filter(entite_id__in=entites_ids)
        
        dashboard_data = {
            'entite': EntiteDetailSerializer(entite).data,
            'statistiques': {
                'total_biens': biens.count(),
                'valeur_totale': biens.aggregate(
                    Sum('valeur_acquisition')
                )['valeur_acquisition__sum'] or 0,
                'valeur_actuelle': biens.aggregate(
                    Sum('valeur_actuelle_cache')
                )['valeur_actuelle_cache__sum'] or 0,
                'nombre_responsables': ResponsableBien.objects.filter(
                    entite_principale=entite
                ).count(),
                'biens_par_statut': dict(
                    biens.values_list('statut').annotate(Count('id'))
                ),
                'biens_par_etat': dict(
                    biens.values_list('etat_physique').annotate(Count('id'))
                ),
            },
            'alertes': {
                'maintenances_en_retard': biens.filter(
                    prochaine_maintenance__lt=datetime.now().date()
                ).count(),
                'garanties_expirees': biens.filter(
                    date_fin_garantie__lt=datetime.now().date()
                ).count(),
                'biens_a_reformer': biens.filter(
                    etat_physique__in=['MAUVAIS', 'HORS_USAGE']
                ).count(),
            },
            'derniers_mouvements': MouvementSerializer(
                MouvementBien.objects.filter(
                    Q(entite_origine=entite) | Q(entite_destination=entite)
                ).order_by('-created')[:10],
                many=True
            ).data
        }
        
        return Response(dashboard_data)


class CategorieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les catégories (lecture seule).
    """
    queryset = Categorie.objects.prefetch_related(
        'sous_categories',
        'enfants'
    ).annotate(
        nombre_biens=Count('biens'),
        nombre_sous_categories=Count('sous_categories')
    )
    serializer_class = CategorieSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'code']
    ordering = ['type', 'ordre', 'nom']
    
    @method_decorator(cache_page(60 * 60))  # Cache 1 heure
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(summary="Arbre des catégories avec sous-catégories")
    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 60))
    def arbre_complet(self, request):
        """Retourne l'arbre complet des catégories et sous-catégories."""
        categories = self.get_queryset().filter(parent__isnull=True)
        
        data = []
        for cat in categories:
            cat_data = {
                'id': str(cat.id),
                'nom': cat.nom,
                'code': cat.code,
                'type': cat.type,
                'icone': cat.icone,
                'couleur': cat.couleur,
                'sous_categories': SousCategorieSerializer(
                    cat.sous_categories.filter(actif=True),
                    many=True
                ).data,
                'enfants': CategorieSerializer(
                    cat.enfants.filter(actif=True),
                    many=True
                ).data
            }
            data.append(cat_data)
        
        return Response(data)


# Filtres personnalisés
class BienFilter(django_filters.FilterSet):
    """Filtres avancés pour les biens."""
    
    valeur_min = django_filters.NumberFilter(
        field_name='valeur_acquisition',
        lookup_expr='gte'
    )
    valeur_max = django_filters.NumberFilter(
        field_name='valeur_acquisition',
        lookup_expr='lte'
    )
    date_acquisition_debut = django_filters.DateFilter(
        field_name='date_acquisition',
        lookup_expr='gte'
    )
    date_acquisition_fin = django_filters.DateFilter(
        field_name='date_acquisition',
        lookup_expr='lte'
    )
    province = django_filters.CharFilter(
        field_name='commune__departement__province__id',
        lookup_expr='exact'
    )
    departement = django_filters.CharFilter(
        field_name='commune__departement__id',
        lookup_expr='exact'
    )
    tags = django_filters.CharFilter(
        method='filter_tags'
    )
    sans_responsable = django_filters.BooleanFilter(
        method='filter_sans_responsable'
    )
    maintenance_en_retard = django_filters.BooleanFilter(
        method='filter_maintenance_en_retard'
    )
    
    class Meta:
        model = Bien
        fields = [
            'statut', 'etat_physique', 'categorie', 
            'sous_categorie', 'entite', 'commune'
        ]
    
    def filter_tags(self, queryset, name, value):
        tags = value.split(',')
        return queryset.filter(tags__overlap=tags)
    
    def filter_sans_responsable(self, queryset, name, value):
        if value:
            return queryset.filter(responsabilites__isnull=True)
        return queryset
    
    def filter_maintenance_en_retard(self, queryset, name, value):
        if value:
            return queryset.filter(
                prochaine_maintenance__lt=datetime.now().date()
            )
        return queryset


class EntiteFilter(django_filters.FilterSet):
    """Filtres pour les entités."""
    
    class Meta:
        model = Entite
        fields = ['type', 'parent', 'commune', 'actif']
