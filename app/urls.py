"""track_and_trace URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static

from . import views

urlpatterns = [
    url(r'^(?P<brand>\w+)/home/$', views.home, name='home'),
    url(r'^login/$', views.login_view, name='login_view'),
    url(r'^(?P<brand>\w+)/upload-plans/$', views.upload_plans, name='upload-plans'),
    url(r'^(?P<brand>\w+)/performance/$', views.performance, name='performance'),
    url(r'^(?P<brand>\w+)/reports-home/$', views.reports_home, name='reports-home'),
    url(r'^(?P<brand>\w+)/bar-chart/$', views.bar_chart, name='bar-chart'),
    url(r'^(?P<brand>\w+)/all-lines/$', views.all_lines, name='all-lines'),
    url(r'^(?P<brand>\w+)/machine_wise_report/$', views.machine_wise_report, name='machine_wise_report'),
    url(r'^(?P<brand>\w+)/shift_wise_report/$', views.shift_wise_report, name='shift_wise_report'),
    url(r'^(?P<brand>\w+)/plant_wise_report/$', views.plant_wise_report, name='plant_wise_report'),
    url(r'^(?P<brand>\w+)/report-download/$', views.report_download, name='report-download'),
    url(r'^(?P<brand>\w+)/plan/$', views.plans, name='plan'),
    url(r'^(?P<brand>\w+)/business-unit/$', views.business_unit, name='business-unit'),
    url(r'^(?P<brand>\w+)/products/$', views.products, name='products'),
    url(r'^(?P<brand>\w+)/machines/$', views.machines, name='machines'),
    url(r'^(?P<brand>\w+)/categories/$', views.categories, name='categories'),
    url(r'^(?P<brand>\w+)/shifts/$', views.shifts, name='shifts'),
    url(r'^(?P<brand>\w+)/upload-business-unit/$', views.upload_business_unit, name='upload-business-unit'),
    url(r'^(?P<brand>\w+)/upload-categories/$', views.upload_categories, name='upload-categories'),
    url(r'^(?P<brand>\w+)/upload-products/$', views.upload_products, name='upload-products'),
    url(r'^(?P<brand>\w+)/upload-product-stocks/$', views.upload_product_stocks, name='upload-product-stocks'),
    url(r'^(?P<brand>\w+)/upload-shift/$', views.upload_shift, name='upload-shifts'),
    url(r'^(?P<brand>\w+)/update_count/$', views.update_count, name='update_count'),
    # url(r'^(?P<brand>\w+)/mailin/$', views.stocks_created, name='stocks_created'),
    url(r'^(?P<brand>\w+)/upload-machines/$', views.upload_machines, name='upload_machines'),
    url(r'^(?P<brand>\w+)/scanning/$', views.scanning, name='scanning'),
    url(r'^logout/', views.logout, name='_logout'),
    url(r'^(?P<brand>\w+)/get_machine_id/', views.get_machine_id, name='get_machine_id'),
    url(r'^(?P<brand>\w+)/get_machine_details/', views.get_machine_details, name='get_machine_details'),
    url(r'^(?P<brand>\w+)/get_shift_id/', views.get_shift_id, name='get_shift_id'),
    url(r'^(?P<brand>\w+)/get_plant_details/', views.get_plant_details, name='get_plant_details'),
    # url(r'^set-user-permission/$', views.set_user_permission, name='set-user-permission'),
    url(r'^(?P<brand>\w+)/user-details/$', views.user_details, name='user-details'),
    url(r'^(?P<brand>\w+)/edit-user-details/(?P<user_id>\w+)/$', views.edit_user_details, name='edit-user-details'),
    url(r'^(?P<brand>\w+)/check_username/$', views.check_username, name='check_username'),
    # url(r'^create_user/$', views.create_user, name='create_user'),
    url(r'^(?P<brand>\w+)/issued_stocks/$', views.issued_stocks, name='issued_stocks'),
    url(r'^(?P<brand>\w+)/issue_product/(?P<productcode>\w+)/$', views.issue_product, name='issue_product'),
    url(r'^(?P<brand>\w+)/download_issued_stocks/$', views.download_issued_stocks, name='download_issued_stocks'),
    url(r'^(?P<brand>\w+)/download-products/$', views.download_products, name='download-products'),
    url(r'^(?P<brand>\w+)/email-log/$', views.email_log, name='email-log'),
    url(r'^(?P<brand>\w+)/add-category/$', views.add_category, name='add_category'),
    url(r'^(?P<brand>\w+)/add-business-unit/$', views.add_business_unit, name='add_business_unit'),
    url(r'^(?P<brand>\w+)/add-machine/$', views.add_machine, name='add_machine'),
    url(r'^(?P<brand>\w+)/add-shift/$', views.add_shift, name='add_shift'),
    url(r'^(?P<brand>\w+)/add-product/$', views.add_product, name='add_product'),
    url(r'^(?P<brand>\w+)/add-plan/$', views.add_plan, name='add_plan'),
    url(r'^(?P<brand>\w+)/add-user/$', views.add_user, name='add_user'),
    url(r'^forgot-password/$', views.forgot_password, name='forgot_password'),
    url(r'^reset-password/(?P<token>[\w-]+)/$', views.reset_password, name='reset_password'),
    url(r'^$', views.login_view, name='login_view'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
