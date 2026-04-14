from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Address, Customer
from .serializers import AddressSerializer, CustomerSerializer


@extend_schema(
    methods=["GET"],
    summary="Lister les clients",
    parameters=[OpenApiParameter(name="email", description="Filtrer par email (insensible à la casse)", required=False, type=str)],
    responses={200: CustomerSerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    summary="Créer un client",
    request=CustomerSerializer,
    responses={201: CustomerSerializer, 400: None},
)
@api_view(["GET", "POST"])
def customer_list(request):
    if request.method == "GET":
        email = request.query_params.get("email")
        queryset = Customer.objects.all()
        if email:
            queryset = queryset.filter(email__iexact=email)
        serializer = CustomerSerializer(queryset, many=True)
        return Response(serializer.data)

    serializer = CustomerSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=["GET"],
    summary="Détail d'un client",
    responses={200: CustomerSerializer, 404: None},
)
@extend_schema(
    methods=["PATCH"],
    summary="Modifier un client",
    request=CustomerSerializer,
    responses={200: CustomerSerializer, 400: None, 404: None},
)
@api_view(["GET", "PATCH"])
def customer_detail(request, pk):
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(CustomerSerializer(customer).data)

    serializer = CustomerSerializer(customer, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=["GET"],
    summary="Lister les adresses d'un client",
    responses={200: AddressSerializer(many=True), 404: None},
)
@extend_schema(
    methods=["POST"],
    summary="Ajouter une adresse à un client",
    request=AddressSerializer,
    responses={201: AddressSerializer, 400: None, 404: None},
)
@api_view(["GET", "POST"])
def customer_addresses(request, pk):
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = AddressSerializer(customer.addresses.all(), many=True)
        return Response(serializer.data)

    serializer = AddressSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(customer=customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=["PATCH"],
    summary="Modifier une adresse",
    request=AddressSerializer,
    responses={200: AddressSerializer, 400: None, 404: None},
)
@api_view(["PATCH"])
def address_detail(request, pk, addr_pk):
    try:
        address = Address.objects.get(pk=addr_pk, customer_id=pk)
    except Address.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = AddressSerializer(address, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
