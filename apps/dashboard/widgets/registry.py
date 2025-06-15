# apps/dashboard/widgets/registry.py
class WidgetRegistry:
    """Registre des widgets disponibles."""
    
    _widgets = {}
    
    @classmethod
    def register(cls, name: str, widget_class):
        """Enregistre un widget."""
        cls._widgets[name] = widget_class
    
    @classmethod
    def get_widget(cls, name: str):
        """Récupère un widget par son nom."""
        return cls._widgets.get(name)
    
    @classmethod
    def list_widgets(cls):
        """Liste tous les widgets disponibles."""
        return list(cls._widgets.keys())