from django.contrib import admin

from app.models import Shift, Product, Machine, BusinessUnit, Planning, Brand, \
    Category, UserBrand, ProductCount, Reason, Stocks, IssuedStocks

admin.site.register(Brand)
admin.site.register(Planning)
admin.site.register(BusinessUnit)
admin.site.register(Machine)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Shift)
admin.site.register(UserBrand)
admin.site.register(ProductCount)
admin.site.register(IssuedStocks)
admin.site.register(Stocks)
admin.site.register(Reason)
