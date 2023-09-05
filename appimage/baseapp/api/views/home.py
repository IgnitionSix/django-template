from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view()
def test(request):
    return Response({"message":"This is a return value from the API!"})