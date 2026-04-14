from django.db import models

class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    customer_id = models.IntegerField() # [cite: 44, 186]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed') # [cite: 45, 67]
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0) # [cite: 46]
    created_at = models.DateTimeField(auto_now_add=True) # [cite: 47]

    def __str__(self):
        return f"Order {self.id}"

class OrderLine(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE) # [cite: 51]
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)