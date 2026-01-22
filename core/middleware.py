from core.models import Store

class StoreAssignmentMiddleware:
    """Ensure all users have a store assigned"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.user.is_authenticated and not request.user.store:
            request.user.store = Store.get_default_store()
            request.user.save(update_fields=['store'])
        
        response = self.get_response(request)
        return response