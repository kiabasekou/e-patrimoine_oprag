# apps/reports/registry.py
class ReportRegistry:
    """Registre des générateurs de rapports."""
    
    _generators = {}
    
    @classmethod
    def register(cls, name: str, generator_class):
        """Enregistre un générateur de rapport."""
        cls._generators[name] = generator_class
    
    @classmethod
    def get_generator(cls, name: str):
        """Récupère un générateur par son nom."""
        return cls._generators.get(name)
    
    @classmethod
    def list_generators(cls):
        """Liste tous les générateurs disponibles."""
        return list(cls._generators.keys())
