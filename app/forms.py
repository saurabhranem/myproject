import datetime
from django import forms
from django.contrib.auth.models import User, Group
from django.core.validators import RegexValidator
from django.db.models import Q

from app.models import Category, BusinessUnit, Machine, Shift, Product, Planning, UserBrand


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Email','name':'email'})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email.lower()).exists():
            raise forms.ValidationError('User with this email does not exist.')
        return email.lower()


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Password'}),
        error_messages={'required': 'Password is required'}
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Confirm password'}),
        error_messages={'required': 'Confirm Password is required'}
    )

    def clean_password(self):
        MIN_LENGTH = 8
        password = self.cleaned_data['password']
        if len(password) < MIN_LENGTH:
            raise forms.ValidationError('The password must be atleast {0} characters long.'.format(
                MIN_LENGTH
            ))
        first_isalpha = password[0].isalpha()
        if all(c.isalpha() == first_isalpha for c in password):
            raise forms.ValidationError("The password must contain at least one letter and at least one digit or special character.")
        return password

    def clean_confirm_password(self):
        try:
            password = self.cleaned_data['password']
            confirm_password = self.cleaned_data['confirm_password']
            if password != confirm_password:
                raise forms.ValidationError('Passwords do not match.')
            return confirm_password
        except:
            password = ''
            confirm_password = self.cleaned_data['confirm_password']
            if password != confirm_password:
                raise forms.ValidationError('Passwords do not match.')
            return confirm_password


class CategoryForm(forms.ModelForm):

    class Meta:
        """
        Category Model
        """
        model = Category
        exclude = ('brand',)


class BusinessUnitForm(forms.ModelForm):

    class Meta:
        """
        Plant Model
        """
        model = BusinessUnit
        exclude = ('brand',)


class MachineForm(forms.ModelForm):
    unit = forms.ModelChoiceField(
        required=True,
        queryset=BusinessUnit.objects.all(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'select-custom-style selectpicker show-tick', 'title': 'select unit',
                                   'data-live-search': "true", })
    )

    class Meta:
        """
        Machine Model
        """
        model = Machine
        exclude = ('brand',)

    def __init__(self, user, *args, **kwargs):
        super(MachineForm, self).__init__(*args, **kwargs)
        self.fields['unit'].queryset = BusinessUnit.objects.filter(brand=user.user_brand.brand)


class ShiftForm(forms.ModelForm):
    start = forms.TimeField(
        widget=forms.TimeInput(
            attrs={'autocomplete': 'off', 'type': 'time', 'placeholder': 'HH:MM (0-23) ex: 22:05'}
        ),
        input_formats=['%H:%M']
    )
    end = forms.TimeField(
        widget=forms.TimeInput(
            attrs={'autocomplete': 'off', 'type': 'time', 'placeholder': 'HH:MM (0-23) ex: 22:05'}
        ),
        input_formats=['%H:%M']
    )

    class Meta:
        """
        Shift Model
        """
        model = Shift
        exclude = ('brand',)

    def clean_shift_no(self):
        clean_shift_no = self.cleaned_data.get('shift_no')
        if Shift.objects.filter(shift_no__iexact=clean_shift_no).exists():
            raise forms.ValidationError('Shift Number already exist. Please enter a different one.')
        return clean_shift_no


class ProductForm(forms.ModelForm):

    category = forms.ModelChoiceField(
        required=True,
        queryset=Category.objects.all(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'select-custom-style selectpicker show-tick', 'title': 'select category',
                                   'data-live-search': "true", })
    )

    class Meta:
        """
        Product Model
        """
        model = Product
        exclude = ('brand',)

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if Product.objects.filter(code__iexact=code).exists():
            raise forms.ValidationError('Product already exist. Please enter a different one.')
        return code

    def __init__(self, user, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(brand=user.user_brand.brand)


class PlanningForm(forms.ModelForm):

    unit = forms.ModelChoiceField(
        required=True,
        queryset=BusinessUnit.objects.all(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'select-custom-style selectpicker show-tick', 'title': 'select unit',
                                   'data-live-search': "true", 'id': "depot_id", })
    )

    shift = forms.ModelChoiceField(
        required=True,
        queryset=Shift.objects.all(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'select-custom-style selectpicker show-tick', 'title': 'select shift',
                                   'data-live-search': "true", })
    )

    product = forms.ModelChoiceField(
        required=True,
        queryset=Product.objects.all(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'select-custom-style selectpicker show-tick', 'title': 'select product',
                                   'data-live-search': "true", })
    )

    machine = forms.ModelChoiceField(
        required=True,
        queryset=Machine.objects.all(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'select-custom-style selectpicker show-tick', 'title': 'select machine',
                                   'data-live-search': "true", 'id': "line_id", })
    )
    str_today = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
    plan_date = forms.DateField(
        widget=forms.DateInput(
            attrs={'autocomplete': 'off', 'type': 'date', 'min': str_today, 'placeholder': 'Plan Date'}
        ),
    )

    class Meta:
        """
        Planning Model
        """
        model = Planning
        exclude = ('brand', 'actual', 'incoming', 'minimum_target')

    # def clean_unit(self):
    #     machine = self.cleaned_data.get('machine')
    #     unit = self.cleaned_data.get('unit')
    #     try:
    #         Machine.objects.get(unit=unit, no=machine.no)
    #     except Machine.DoesNotExist:
    #         raise forms.ValidationError('Please select the correct plant for selected machine')
    #     return unit

    def clean_plan_date(self):
        machine = self.cleaned_data.get('machine')
        unit = self.cleaned_data.get('unit')
        shift = self.cleaned_data.get('shift')
        plan_date = self.cleaned_data.get('plan_date')
        try:
            Planning.objects.get(unit=unit, machine=machine, shift=shift, plan_date=plan_date)
            raise forms.ValidationError('Plan already Exist')
        except Planning.DoesNotExist:
            pass
        return plan_date

    def __init__(self, user, *args, **kwargs):
        super(PlanningForm, self).__init__(*args, **kwargs)
        self.fields['unit'].queryset = BusinessUnit.objects.filter(brand=user.user_brand.brand)
        self.fields['shift'].queryset = Shift.objects.filter(brand=user.user_brand.brand)
        self.fields['product'].queryset = Product.objects.filter(brand=user.user_brand.brand)
        self.fields['machine'].queryset = Machine.objects.filter(brand=user.user_brand.brand)


class UserBrandForm(forms.Form):
    user_id = forms.CharField(
        required=False
    )
    image_url = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'id': "avatar", 'type': "file", 'class': "file-loading", 'accept': ".jpg,.png,.jpeg"})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.TextInput(attrs={'autocomplete': 'off',
                                      'placeholder': 'email', 'type': "email"}),
        error_messages={'required': 'Email is required'}
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={'autocomplete': 'off', 'placeholder': 'first name'}),
        error_messages={'required': 'First Name is required'}
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={'autocomplete': 'off', 'placeholder': 'last name'}),
        error_messages={'required': 'Last Name is required'}
    )
    group = forms.ModelChoiceField(
        required=True,
        queryset=Group.objects.all().exclude(name__icontains="Superadmin"),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'select-custom-style selectpicker show-tick', 'title': 'select group',
                                   'data-live-search': "true", })
    )
    unit = forms.ModelMultipleChoiceField(
        required=False,
        queryset=BusinessUnit.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select-custom-style show-tick unit_select', 'title': 'select unit',
                                           'data-live-search': "true", 'id': 'depot_id'})
    )
    machine = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Machine.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select-custom-style selectpicker show-tick', 'title': 'select machine',
                                           'data-live-search': "true", 'id': 'line_id'})
    )
    mobile_number = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={'autocomplete': 'off', 'type': 'number', 'placeholder': 'Mobile Number'}),
        validators=[
            RegexValidator('^[0-9]{10,10}$', message="it should be 10 digits.")],
    )

    class Meta:
        """
        Planning Model
        """
        model = UserBrand
        exclude = ('brand', 'user')

    def __init__(self, user, *args, **kwargs):
        super(UserBrandForm, self).__init__(*args, **kwargs)
        self.fields['unit'].queryset = BusinessUnit.objects.filter(brand=user.user_brand.brand)
        self.fields['machine'].queryset = Machine.objects.filter(brand=user.user_brand.brand)

    def clean_email(self):
        user_id = self.cleaned_data.get('user_id')
        email = self.cleaned_data.get('email')
        existing_object = UserBrand.objects.filter(user__email=email)
        if user_id != "":
            existing_object = existing_object.exclude(user_id=user_id)
    
        if existing_object.exists():
            raise forms.ValidationError('Email address is already in use. Please enter a different one.')
        else:
            return email

    def clean_mobile_number(self):
        user_id = self.cleaned_data.get('user_id')
        mobile_number = self.cleaned_data.get('mobile_number')
        existing_object = UserBrand.objects.filter(mobile_number=mobile_number)
        if user_id != "":
            existing_object = existing_object.exclude(user_id=user_id)

        if existing_object.exists():
            raise forms.ValidationError('Mobile number is already in use. Please enter a different one.')
        else:
            return mobile_number

    # def clean_machine(self):
    #     machine = self.cleaned_data['machine']
    #     unit = self.cleaned_data.get('unit')
    #     for each in machine:
    #         try:
    #             Machine.objects.get(unit=unit[0], no=each.no)
    #         except Machine.DoesNotExist:
    #             raise forms.ValidationError('Please select the correct machine for Selected Unit')
    #     return machine