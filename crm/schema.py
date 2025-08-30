import re
import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from .models import Customer, Product, Order

import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Product, Order
from crm.models import Product
from .filters import CustomerFilter, ProductFilter, OrderFilter


# --------------------
# Types with Relay Node
# --------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        fields = ("id", "name", "email", "phone", "created_at")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        fields = ("id", "customer", "products", "total_amount", "order_date")


# --------------------
# Queries with Filters
# --------------------
class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter, order_by=graphene.List(of_type=graphene.String))
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter, order_by=graphene.List(of_type=graphene.String))
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter, order_by=graphene.List(of_type=graphene.String))

    total_customers = graphene.Int()
    total_orders = graphene.Int()
    total_revenue = graphene.Float()

    def resolve_all_customers(self, info, **kwargs):
        qs = Customer.objects.all()
        order_by = kwargs.get("order_by")
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_products(self, info, **kwargs):
        qs = Product.objects.all()
        order_by = kwargs.get("order_by")
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_orders(self, info, **kwargs):
        qs = Order.objects.all()
        order_by = kwargs.get("order_by")
        if order_by:
            qs = qs.order_by(*order_by)
        return qs
        
    def resolve_total_customers(root, info):
        # Returns the total count of customers.
        return Customer.objects.count()

    def resolve_total_orders(root, info):
        # Returns the total count of orders.
        return Order.objects.count()

    def resolve_total_revenue(root, info):
        # Calculates the sum of 'total_amount' across all orders.
        # The result might be None if there are no orders, so we default to 0.
        aggregation = Order.objects.aggregate(total_revenue=Sum('total_amount'))
        return aggregation['total_revenue'] or 0.0

# -------------------------
# Object Types
# -------------------------
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# -------------------------
# Mutations
# -------------------------
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # Email uniqueness validation
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists")

        # Phone validation
        if phone:
            phone_pattern = re.compile(r"^\+?\d[\d\-]+$")
            if not phone_pattern.match(phone):
                raise Exception("Invalid phone format")

        customer = Customer(name=name, email=email, phone=phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully!")


# class BulkCreateCustomers(graphene.Mutation):
#     class Arguments:
#         customers = graphene.List(
#             graphene.NonNull(
#                 graphene.InputObjectType(
#                     "CustomerInput",
#                     name=graphene.String(required=True),
#                     email=graphene.String(required=True),
#                     phone=graphene.String(),
#                 )
#             )
#         )

#     customers = graphene.List(CustomerType)
#     errors = graphene.List(graphene.String)

#     @transaction.atomic
#     def mutate(self, info, customers):
#         created = []
#         errors = []

#         for c in customers:
#             try:
#                 if Customer.objects.filter(email=c.email).exists():
#                     errors.append(f"Email already exists: {c.email}")
#                     continue
#                 customer = Customer(name=c.name, email=c.email, phone=c.phone or "")
#                 customer.full_clean()
#                 customer.save()
#                 created.append(customer)
#             except ValidationError as e:
#                 errors.append(f"{c.email}: {str(e)}")

#         return BulkCreateCustomers(customers=created, errors=errors)

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, customers):
        created = []
        errors = []

        for c in customers:
            try:
                if Customer.objects.filter(email=c.email).exists():
                    errors.append(f"Email already exists: {c.email}")
                    continue
                customer = Customer(name=c.name, email=c.email, phone=c.phone or "")
                customer.full_clean()
                customer.save()
                created.append(customer)
            except ValidationError as e:
                errors.append(f"{c.email}: {str(e)}")

        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be positive")
        if stock < 0:
            raise Exception("Stock cannot be negative")

        product = Product(name=name, price=price, stock=stock)
        product.save()
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        if not product_ids:
            raise Exception("At least one product must be selected")

        products = Product.objects.filter(id__in=product_ids)
        if len(products) != len(product_ids):
            raise Exception("One or more product IDs are invalid")

        with transaction.atomic():
            order = Order(customer=customer)
            order.save()
            order.products.set(products)
            order.total_amount = sum([p.price for p in products])
            order.save()

        return CreateOrder(order=order)


# -------------------------
# Query + Mutation Root
# -------------------------
class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.all()


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

class UpdateLowStockProducts(graphene.Mutation):
    """
    Finds all products with stock less than 10, increments their stock
    by 10, and returns the list of updated products.
    """
    class Arguments:
        # No arguments needed as the logic is predefined
        pass

    # Define the output fields of the mutation
    updated_products = graphene.List(ProductType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info):
        # Find products with stock less than 10
        low_stock_products = Product.objects.filter(stock__lt=10)
        
        if not low_stock_products.exists():
            return UpdateLowStockProducts(updated_products=[], message="No low-stock products found to update.")

        # Atomically increment the stock by 10 for all found products
        # Using F() prevents race conditions and is more efficient.
        low_stock_products.update(stock=F('stock') + 10)

        # Refresh the queryset from the database to get the new stock values
        updated_products_qs = Product.objects.filter(pk__in=low_stock_products.values_list('pk', flat=True))
        
        count = updated_products_qs.count()
        message = f"Successfully restocked {count} low-stock product(s)."

        return UpdateLowStockProducts(updated_products=list(updated_products_qs), message=message)
