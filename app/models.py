from __future__ import unicode_literals

from django.db import models

from app.utils import update_filename, update_logo


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserBrand(BaseModel):
    user = models.OneToOneField('auth.User', related_name='user_brand')
    brand = models.ForeignKey('Brand')
    group = models.ForeignKey('auth.Group')
    unit = models.ManyToManyField('BusinessUnit', blank=True)
    machine = models.ManyToManyField('Machine', blank=True)
    image_url = models.ImageField(upload_to=update_filename, max_length=200,
                                  null=True, blank=True, default="profile/profile-default.png")
    mobile_number = models.CharField(max_length=10)

    def get_machine_detail(obj):
        if obj.machine.all():
            machines = obj.machine.all()
            machines_details = []
            for each in machines:
                machines_details.append("{0} - {1}".format(str(each.no), str(each.name)))
            return machines_details

    def get_unit_detail(obj):
        if obj.unit.all():
            units = obj.unit.all()
            unit_details = []
            for each in units:
                unit_details.append("{0} - {1}".format(str(each.code), str(each.name)))
            return unit_details

    def __unicode__(self):
        return "{} - {}".format(self.user, self.brand)


class Brand(BaseModel):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to=update_logo, max_length=200,
                             null=True, blank=True, default="profile/gm.png")

    def __unicode__(self):
        return "{}".format(self.name)


class Shift(BaseModel):
    name = models.CharField(max_length=100)
    shift_no = models.CharField(max_length=16, unique=True)
    start = models.TimeField()
    end = models.TimeField()
    brand = models.ForeignKey('Brand')

    def __unicode__(self):
        return "{}".format(self.name)


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(UserBrand, related_name='email_verification_token')
    token = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_till = models.DateTimeField()
    verified = models.BooleanField(default=False)
    type = models.CharField(max_length=10, choices=(('0', 'Verification'), ('1', 'Forgot password')), default='0')

    def __str__(self):
        return '{0} - {1}'.format(self.user.user.email, self.token)

    class Meta:
        verbose_name_plural = 'Email Verification Tokens'


class Category(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    brand = models.ForeignKey('Brand')

    class Meta:
        verbose_name_plural = "Categories"

    def __unicode__(self):
        return "{} - {}".format(self.code, self.name)


class Product(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    category = models.ForeignKey('Category')
    brand = models.ForeignKey('Brand')

    def __unicode__(self):
        return "{} - {}".format(self.code, self.name)

    def get_total_stocks(self, ):
        try:
            product_Stocks = Stocks.objects.get(product=self)
            total = product_Stocks.available_stocks
        except:
            total = 0
        return total


class Machine(BaseModel):
    name = models.CharField(max_length=255)
    no = models.CharField(max_length=16)
    make = models.CharField(max_length=100)
    brand = models.ForeignKey('Brand')
    unit = models.ForeignKey('BusinessUnit')

    def __unicode__(self):
        return "{} - {} - {}".format(self.no, self.name, self.unit.name)


class BusinessUnit(BaseModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    code = models.CharField(max_length=255, unique=True)
    brand = models.ForeignKey('Brand')

    # HEADOFFICE = 'HO'
    # REGIONALOFFICE = 'RO'
    # BRANCHOFFICE = 'BO'
    # BUSINESS_UNIT_TYPE_CHOICES = (
    #     (HEADOFFICE, 'HeadOffice'),
    #     (BRANCHOFFICE, 'BranchOffice'),
    #     (REGIONALOFFICE, 'RegionalOffice'),
    # )
    # type = models.CharField(
    #     max_length=2,
    #     choices=BUSINESS_UNIT_TYPE_CHOICES,
    #     default=BRANCHOFFICE,
    # )

    def __unicode__(self):
        return "{}".format(self.name)


class Planning(BaseModel):
    shift = models.ForeignKey('Shift')
    machine = models.ForeignKey('Machine')
    product = models.ForeignKey('Product')
    brand = models.ForeignKey('Brand')
    unit = models.ForeignKey('BusinessUnit')
    plan_date = models.DateField()
    target = models.IntegerField(default=0)
    incoming = models.IntegerField(default=0)
    actual = models.IntegerField(default=0)
    minimum_target = models.IntegerField(default=0)

    def __unicode__(self):
        return "{} - {} - {} - {}".format(self.plan_date, self.machine.no, self.machine.name, self.machine.unit.name)


class Reason(BaseModel):
    plan = models.ForeignKey('Planning')
    minimum_target_per_hour = models.IntegerField()
    achieved_count_per_hour = models.IntegerField()
    time = models.CharField(max_length=20)
    reason = models.CharField(max_length=255, null=True)
    given_by = models.ForeignKey('UserBrand')
    brand = models.ForeignKey('Brand')

    def __unicode__(self):
        return "{} - {} -{} - {}".format(self.plan.plan_date, self.plan.machine.name,
                                         self.plan.machine.name, self.plan.unit.name)


class ProductCount(BaseModel):
    plan_details = models.ForeignKey('Planning')
    count = models.IntegerField(default=0)
    given_by = models.ForeignKey('UserBrand')
    brand = models.ForeignKey('Brand')

    def __unicode__(self):
        return "{} - {}".format(self.plan_details.plan_date, self.count)


class Stocks(BaseModel):
    product = models.ForeignKey('Product')
    available_stocks = models.IntegerField(default=0)
    brand = models.ForeignKey('Brand')

    def __unicode__(self):
        return "{} - {}".format(self.product.code, self.available_stocks)


class IssuedStocks(BaseModel):
    product = models.ForeignKey('Product')
    issued_stocks = models.IntegerField(default=0)
    remarks = models.CharField(max_length=255)
    issued_by = models.ForeignKey('UserBrand')
    brand = models.ForeignKey('Brand')

    def __unicode__(self):
        return "{} - {}".format(self.product.code, self.issued_stocks)


class EmailLog(BaseModel):
    subject = models.TextField()
    message = models.TextField()
    sender = models.CharField(max_length=100)
    receiver = models.CharField(max_length=100)
    cc = models.TextField()
    brand = models.ForeignKey('Brand')

    def __unicode__(self):
        return "{} - {}".format(self.created_at, self.receiver)