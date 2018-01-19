import csv
import datetime
import fnmatch
import json
import smtplib
import uuid

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.template import Context
from django.template.loader import get_template
from django.urls import reverse
from django.utils.timesince import timesince
from dateutil.relativedelta import relativedelta
from django.db import transaction
from time import strftime
import datetime
from app import constants
from app.forms import ResetPasswordForm, ForgotPasswordForm, CategoryForm, BusinessUnitForm, MachineForm, ShiftForm, \
    ProductForm, PlanningForm, UserBrandForm
from app.models import *
from track_and_trace import settings


def login_view(request):
    try:
        if request.method == 'GET':
            if request.user.is_authenticated():
                return redirect(reverse("home", kwargs={'brand': request.user.user_brand.brand.name}))
            return render(request, 'login.html')
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                login(request, user)
                return redirect(reverse("home", kwargs={'brand': user.user_brand.brand.name}))
            else:
                messages.error(request, 'Invalid Credentials! Please Try Again')
                return redirect('/')
    except UserBrand.DoesNotExist:
        user_brand = "create user brand"
    context = {
        'user_brand': user_brand,
    }
    return render(request, 'login.html', context)


@login_required
def home(request, brand):
    groups = request.user.groups.all()
    context = {
        # 'plans': plans,
        'groups': groups,
        'brand': brand,
    }
    return render(request, 'home.html', context)


def get_business_detail(request, brand):
    if request.user.user_brand.group.name == 'SuperAdmin':
        business_unit_details = BusinessUnit.objects.all().order_by('-id')
    elif request.user.user_brand.group.name == 'Admin':
        business_unit_details = BusinessUnit.objects.filter(brand__name=brand).order_by('-id')
    elif request.user.user_brand.group.name == 'PlantAdmin':
        business_unit_details = BusinessUnit.objects.filter(id__in=request.user.user_brand.unit.all()).order_by('-id')
    elif request.user.user_brand.group.name == 'SuperVisor':
        business_unit_details = BusinessUnit.objects.filter(id=request.user.user_brand.unit.all()[0].id).order_by('-id')
    elif request.user.user_brand.group.name == 'ReadOnly':
        business_unit_details = BusinessUnit.objects.filter(brand__name=brand).order_by('-id')
    else:
        business_unit_details = []
    return business_unit_details


def user_based_get_machine_details(request, brand):
    if request.user.user_brand.group.name == 'SuperAdmin':
        machine_details = Machine.objects.all().order_by('-id')
    elif request.user.user_brand.group.name == 'Admin':
        machine_details = Machine.objects.filter(brand__name=brand)
    elif request.user.user_brand.group.name == 'PlantAdmin':
        machine_details = Machine.objects.filter(unit__id__in=request.user.user_brand.unit.all())
    elif request.user.user_brand.group.name == 'SuperVisor':
        machine_details = Machine.objects.filter(id__in=request.user.user_brand.machine.all())
    elif request.user.user_brand.group.name == 'ReadOnly':
        machine_details = Machine.objects.filter(brand__name=brand)
    else:
        machine_details = []
    return machine_details


@login_required
def scanning(request, brand):
    dropdown_reasons = constants.reasons
    business_unit_details = get_business_detail(request, brand)
    today = datetime.datetime.now()
    if request.GET.get('date'):
        date = datetime.datetime.strptime(request.GET.get('date'), "%Y/%m/%d %H:%M").date()
    else:
        date = None
    machine_no = request.GET.get('machine_no')
    shift_no = request.GET.get('shift_no')
    depot_code = request.GET.get('depot_code')
    try:
        if date and depot_code and machine_no:
            unit_details = BusinessUnit.objects.get(id=depot_code)
            plan_date = date
            shift_details = Shift.objects.get(shift_no=shift_no)
            machine_details = Machine.objects.get(no=machine_no, unit=unit_details)
            plans = Planning.objects.get(plan_date=plan_date,
                                         unit=unit_details,
                                         machine=machine_details,
                                         shift=shift_details)
            reasons = Reason.objects.filter(plan__plan_date=plan_date,
                                            plan__unit=unit_details,
                                            plan__machine=machine_details,
                                            plan__shift=shift_details).order_by('-id')

        else:
            context = {
                'dropdown_reasons': dropdown_reasons,
                'business_unit_details': business_unit_details,
                'brand': brand,
            }
            return render(request, 'scanning.html', context)

    except Planning.DoesNotExist:
        plans = "No Data"
        reasons = "No Data"
    context = {
        'plans': plans,
        'reasons': reasons,
        'brand': brand,
        'dropdown_reasons': dropdown_reasons,
        'business_unit_details': business_unit_details,
    }
    return render(request, 'scanning.html', context)


def get_machine_id(request, brand):
    resp, success, machine_items = {}, False, []
    depot_code = request.GET.get("id")
    try:
        if request.user.user_brand.group.name == 'SuperVisor':
            machine = Machine.objects.filter(id__in=request.user.user_brand.machine.all(),
                                             unit__code=depot_code,
                                             )
        else:
            machine = Machine.objects.filter(unit__code=depot_code)
        for i in machine:
            temp_dict = {}
            temp_dict["name"] = i.name
            temp_dict["no"] = i.no
            machine_items.append(temp_dict)
        success = True
    except Machine.DoesNotExist:
        success = False
    resp["success"] = success
    resp["machine_items"] = machine_items
    return JsonResponse(resp)


def get_shift_id(request, brand):
    resp, success, shift_items = {}, False, []
    depot_code = request.GET.get("depot_code")
    try:
        shift = Shift.objects.filter(brand__name=brand)
        for i in shift:
            temp_dict = {}
            temp_dict["name"] = i.name
            temp_dict["shift_no"] = i.shift_no
            shift_items.append(temp_dict)
        success = True
    except Shift.DoesNotExist:
        success = False
    resp["success"] = success
    resp["shift_items"] = shift_items
    return JsonResponse(resp)


@login_required
def update_count(request, brand=None,):
    import ipdb; ipdb.set_trace()
    response, success = {}, False
    today = datetime.datetime.now()
    plan_id = request.POST.get("planid")
    count = int(request.POST.get("qr_code"))
    reason_str = request.POST.get('reason')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    brand = Brand.objects.get(name=brand)
    try:
        planning = Planning.objects.get(id=plan_id)
        planning.actual = planning.actual + count
        planning.save()
        scanned_product = ProductCount.objects.create(plan_details=planning,
                                                      count=count,
                                                      given_by=request.user.user_brand, brand=brand
                                                      )
        stocks_update, status = Stocks.objects.get_or_create(product=planning.product, brand=brand)
        stocks_update.available_stocks = stocks_update.available_stocks + count
        stocks_update.save()
        # if reason_str:
        reason_str = reason_str
        start_time = start_time
        end_time = end_time
        # if start_time == 23:
        #     next_hour = 0
        #     timer = "{0}-{1}".format(time, next_hour)
        #     reason = Reason.objects.create(plan=planning, time=timer,
        #                                    minimum_target_per_hour=planning.minimum_target,
        #                                    given_by=request.user.user_brand,reason=reason_str,
        #                                    achieved_count_per_hour=count, brand=brand)
        timer = "{0}-{1}".format(start_time, end_time)
        reason = Reason.objects.create(plan=planning, time=timer,
                                       minimum_target_per_hour=planning.minimum_target,
                                       given_by=request.user.user_brand,reason=reason_str,
                                       achieved_count_per_hour=count, brand=brand)
        # else:
        #     reason = None
        if planning.minimum_target > count:
            min_target_not_achieved_mail(planning, reason)
        msg = " Reason Updated Successfully"
        success = True
    except Reason.DoesNotExist:
        success = False
        msg = "Reason Not Updated"
    response['success'] = success
    response['actual_count'] = planning.actual
    response['message'] = msg
    return HttpResponse(json.dumps(response))


def min_target_not_achieved_mail(planning, reason):
    plant_admin_mail_id = UserBrand.objects.filter(group__name='PlantAdmin',
                                                   unit=planning.unit).values_list('user__email', flat=True)
    cc_email = UserBrand.objects.filter((Q(group__name='SuperVisor') & Q(machine=planning.machine)) |
                                        Q(group__name='Admin')
                                        )
    cc_email_list = []
    for each in cc_email:
        cc_email_list.append(each.user.email)
    receiver = plant_admin_mail_id
    sender = 'Gladminds'
    subject = 'Issue in {0} at {1} on {2}'.format(planning.machine.name,
                                                  planning.unit.name,
                                                  planning.plan_date)
    body = "Dear Team,\n\n" \
           "Fail to achieve the minimum target. Due to the following issue," \
           "Issue: {0}\n" \
           "Machine: {1} - {2}\n" \
           "Achieved: {3}\n" \
           "Minimum Target: {4}\n" \
           "Shift: {5}\n" \
           "Plat: {6} - {7}\n" \
           "Time: {8}\n" \
           "Raised by:{9}.\n\n\n" \
           "Regards,\n" \
           "Gladminds".format(reason.reason, planning.machine.no, planning.machine.name,
                              reason.achieved_count_per_hour, reason.minimum_target_per_hour, planning.shift.shift_no,
                              planning.unit.code, planning.unit.name, datetime.datetime.now(),
                              reason.given_by)
    try:
        toaddr = receiver
        cc = cc_email_list
        fromaddr = sender
        message_subject = subject
        message_text = body
        message = "From: %s\r\n" % fromaddr \
                  + "To: %s\r\n" % toaddr \
                  + "CC: %s\r\n" % ",".join(cc) \
                  + "Subject: %s\r\n" % message_subject \
                  + "\r\n" \
                  + message_text
        toaddrs = [toaddr] + cc
        server = smtplib.SMTP(settings.EMAIL_HOST)
        server.starttls()
        server.set_debuglevel(1)
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(fromaddr, toaddrs, message)
        server.quit()
        EmailLog.objects.create(subject=subject, message=message, sender=sender, receiver=receiver, cc=cc)
        return True
    except Exception as ex:
        return False


def plan_details(date, depot_code):
    unit_details = BusinessUnit.objects.get(code=depot_code)
    plan_date = datetime.datetime.strptime(date, "%Y/%m/%d %H:%M").date()
    plans = Planning.objects.filter(plan_date=plan_date,
                                    unit=unit_details).order_by('machine__no')
    if not plans:
        plans = 'No Data'
    return plans, unit_details


@login_required
def reports_home(request, brand=None):
    return render(request, 'reports-home.html', {'brand': brand})


@login_required
def report_download(request, brand=None):
    from_date_report = request.GET.get('from_date')
    to_date_report = request.GET.get('to_date')
    depot_code = request.GET.get('depot_code')
    page = request.GET.get('page')
    business_unit_details = get_business_detail(request, brand)
    if from_date_report and to_date_report and depot_code:
        unit_details = BusinessUnit.objects.get(code=depot_code)
        try:
            from_date = datetime.datetime.strptime(from_date_report, "%Y/%m/%d %H:%M").date()
            to_date = datetime.datetime.strptime(to_date_report, "%Y/%m/%d %H:%M").date()
        except:
            from_date = datetime.datetime.strptime(from_date_report, "%Y/%m/%d").date()
            to_date = datetime.datetime.strptime(to_date_report, "%Y/%m/%d").date()
        if request.GET.get('report_download'):
            plans = Planning.objects.filter(plan_date__range=(from_date, to_date),
                                            unit=unit_details).order_by('plan_date')
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] \
                = 'attachment; filename="SamplePlanFile.csv"'
            writer = csv.writer(response, dialect=csv.excel)
            writer.writerow(['Unit Code', 'Unit Name', 'Shift No',
                             'Machine', 'Product', 'Plan Date', 'Target', 'Actual', 'Reason'])
            for plan in plans:
                row_list = []
                row_list.append(plan.unit.code)
                row_list.append(plan.unit.name)
                row_list.append(plan.shift.shift_no+"-"+plan.shift.name)
                row_list.append((plan.machine.no+"-"+plan.machine.name))
                row_list.append((plan.product.code+"-"+plan.product.name))
                row_list.append(plan.plan_date)
                row_list.append(plan.target)
                row_list.append(plan.actual)
                if Reason.objects.filter(plan=plan):
                    reasons_list = []
                    reasons = Reason.objects.filter(plan=plan)
                    i = 1
                    for reason in reasons:
                        if reason.reason:
                            reasons_list.append("{0}.{1}({2} {3}:{4})".format(
                                i, reason.reason, str(reason.created_at.date()),
                                str((reason.created_at + datetime.timedelta(hours=5, minutes=30)).hour),
                                str((reason.created_at + datetime.timedelta(hours=5, minutes=30)).minute)))
                            i = i+1
                    row_list.append(reasons_list)
                writer.writerow(row_list)
            return response
        else:
            plans = Planning.objects.filter(plan_date__range=(from_date, to_date),
                                            unit=unit_details).order_by('plan_date',
                                                                        )
            plans, pagination_info = get_paginated_objects(plans, page, 10)
            if plans == "No Data":
                plan_list = plans
            plan_list = []
            i = 1
            p = 1
            if plans != "No Data":
                for plan in plans:
                    row_list = {}
                    row_list["unit_code"] = plan.unit.code
                    row_list["unit_name"] = plan.unit.name
                    row_list["shift"] = plan.shift.shift_no+"-"+plan.shift.name
                    row_list["machine"] = plan.machine.no+"-"+plan.machine.name
                    row_list["product"] = plan.product.code+"-"+plan.product.name
                    row_list["plan_date"] = plan.plan_date
                    row_list["target"] = plan.target
                    row_list["actual"] = plan.actual
                    reasons_list = []
                    reasons = Reason.objects.filter(plan=plan)
                    if reasons:
                        for reason in reasons:
                            if reason.reason:
                                p = i
                                reasons_list.append("{0}.{1}({2} {3}:{4})".format(
                                    i, reason.reason, str(reason.created_at.date()),
                                    str((reason.created_at + datetime.timedelta(hours=5, minutes=30)).hour),
                                    str((reason.created_at + datetime.timedelta(hours=5, minutes=30)).minute)))
                                i = i+1
                        row_list["reasons"] = reasons_list
                    plan_list.append(row_list)
            if not plan_list:
                plan_list = "No Data"
            return render(request, 'reports.html',
                          {'plans': plan_list,
                           'from_date': from_date_report,
                           'to_date': to_date_report,
                           'colspan': p,
                           'shift': shifts,
                           'brand': brand,
                           'depot_code': depot_code,
                           'plant_details': unit_details,
                           'business_unit_details': business_unit_details,
                           'pagination_info': pagination_info,
                           }
                          )
    else:
        return render(request, 'reports.html',
                      {'business_unit_details': business_unit_details,
                           'brand': brand})


@login_required
def plans(request, brand):
    page = request.GET.get('page')
    today = datetime.datetime.now()
    depot_code = request.GET.get('depot_code')
    business_unit_details = get_business_detail(request, brand)
    if depot_code:
        unit_details = BusinessUnit.objects.get(code=depot_code)
        next_seven_days = today + datetime.timedelta(days=7)
        plans = Planning.objects.filter(plan_date__range=(today, next_seven_days),
                                        unit=unit_details).order_by('plan_date')
        plans, pagination_info = get_paginated_objects(plans, page, 10)
        if not plans:
            plans = 'No Data'
        return render(request, 'plans.html',
                      {'plans': plans,
                       'depot_code': depot_code,
                       'brand': brand,
                       'plant_details': unit_details,
                       'business_unit_details': business_unit_details,
                       'pagination_info': pagination_info,})
    else:
        return render(request, 'plans.html',
                      {'business_unit_details': business_unit_details,
                       'brand': brand,
                       })


@login_required
def shift_wise_report(request, brand):
    from_date_report = request.GET.get('from_date')
    to_date_report = request.GET.get('to_date')
    depot_code = request.GET.get('depot_code')
    shift_id = request.GET.get('shift_no')
    shift_details = Shift.objects.filter(brand__name=brand)
    business_unit_details = get_business_detail(request, brand)
    if from_date_report and to_date_report and depot_code:
        unit_details = BusinessUnit.objects.get(code=depot_code)
        try:
            from_date = datetime.datetime.strptime(from_date_report, "%Y/%m/%d %H:%M").date()
            to_date = datetime.datetime.strptime(to_date_report, "%Y/%m/%d %H:%M").date()
        except:
            from_date = datetime.datetime.strptime(from_date_report, "%Y/%m/%d").date()
            to_date = datetime.datetime.strptime(to_date_report, "%Y/%m/%d").date()
        plant_name = unit_details.name
        unit_plans = Planning.objects.filter(plan_date__range=(from_date, to_date),
                                             unit=unit_details, shift__shift_no=shift_id).order_by('plan_date')
        machines = Machine.objects.filter(unit__code=depot_code)
        plans = []
        if unit_plans:
            for machine in machines:
                if unit_plans.filter(machine=machine):
                    plans_by_machines = unit_plans.filter(machine=machine)
                    target_list = plans_by_machines.values_list('target', flat=True)
                    total_target = sum(target_list)
                    achieved_list = plans_by_machines.values_list('actual', flat=True)
                    total_achieved = sum(achieved_list)
                    performance = {}
                    performance["machine"] = str(plans_by_machines[0].machine.no+"-"+plans_by_machines[0].machine.name+ "-" +
                                                 plans_by_machines[0].shift.shift_no + "-" + plans_by_machines[0].shift.name)
                    performance["target"] = str(total_target)
                    performance["actual"] = str(total_achieved)
                    plans.append(performance)
                plans_list = json.dumps(plans)
        if not plans:
            plans_list = 'No Data'

        return render(request, 'shift_wise_report.html',
                      {'plans': plans_list,
                       'from_date': from_date_report,
                       'to_date': to_date_report,
                       'depot_code': depot_code,
                       'shift_no': shift_id,
                       'brand': brand,
                       'shift_details': shift_details,
                       'plant_name': plant_name,
                       'business_unit_details': business_unit_details})
    else:
        return render(request, 'shift_wise_report.html',
                      {'business_unit_details': business_unit_details,
                       'brand': brand,'shift_details': shift_details})


@login_required
def machine_wise_report(request, brand):
    from_date_report = request.GET.get('from_date')
    to_date_report = request.GET.get('to_date')
    depot_code = request.GET.get('depot_code')
    machine_id = request.GET.get('machine_no')
    business_unit_details = get_business_detail(request, brand)
    if depot_code:
        machine_details = Machine.objects.filter(unit__id=depot_code)
    else:
        machine_details = []
    try:
        if from_date_report and to_date_report and depot_code:
            unit_details = BusinessUnit.objects.get(id=depot_code)
            try:
                from_date = datetime.datetime.strptime(from_date_report, "%Y/%m/%d %H:%M").date()
                to_date = datetime.datetime.strptime(to_date_report, "%Y/%m/%d %H:%M").date()
            except:
                from_date = datetime.datetime.strptime(from_date_report, "%Y/%m/%d").date()
                to_date = datetime.datetime.strptime(to_date_report, "%Y/%m/%d").date()
            plant_name = unit_details.name
            unit_plans = Planning.objects.filter(plan_date__range=(from_date, to_date),
                                                 unit=unit_details, machine__id=machine_id).order_by('plan_date')
            shifts = Shift.objects.filter(brand__name=brand)
            plans = []
            if unit_plans:
                for shift in shifts:
                    if unit_plans.filter(shift=shift):
                        plans_by_shifts = unit_plans.filter(shift=shift)
                        target_list = plans_by_shifts.values_list('target', flat=True)
                        total_target = sum(target_list)
                        achieved_list = plans_by_shifts.values_list('actual', flat=True)
                        total_achieved = sum(achieved_list)
                        performance = {}
                        performance["machine"] = str(plans_by_shifts[0].machine.no+"-"+plans_by_shifts[0].machine.name+ "-" +
                                                     plans_by_shifts[0].shift.shift_no + "-" + plans_by_shifts[0].shift.name)
                        performance["target"] = str(total_target)
                        performance["actual"] = str(total_achieved)
                        plans.append(performance)
                    plans_list = json.dumps(plans)
            if not plans:
                plans_list = 'No Data'
            return render(request, 'machine_wise_report.html',
                          {'plans': plans_list,
                           'from_date': from_date_report,
                           'to_date': to_date_report,
                           'depot_code': depot_code,
                           'machine_no': machine_id,
                           'machine_details': machine_details,
                           'plant_name': plant_name,
                           'brand': brand,
                           'business_unit_details': business_unit_details})
        else:
            return render(request, 'machine_wise_report.html',
                          {'business_unit_details': business_unit_details,
                           'brand': brand})
    except BusinessUnit.DoesNotExist:
        plans = "no data"
    context = {
            'brand': brand,
        }
    return render(request, 'machine_wise_report.html', context)


def plant_wise_report(request, brand):
    from_date_report = request.GET.get('from_date')
    to_date_report = request.GET.get('to_date')
    depot_code = request.GET.get('depot_code')

    if depot_code:
        plant_details = BusinessUnit.objects.filter(code=depot_code)
    else:
        plant_details = []
    business_unit_details = get_business_detail(request, brand)
    if from_date_report and to_date_report and depot_code:
        unit_details = BusinessUnit.objects.get(code=depot_code)
        try:
            from_date = datetime.datetime.strptime(from_date_report, "%Y/%m/%d %H:%M").date()
            to_date = datetime.datetime.strptime(to_date_report, "%Y/%m/%d %H:%M").date()
        except:
            from_date = datetime.datetime.strptime(from_date_report, "%Y/%m/%d").date()
            to_date = datetime.datetime.strptime(to_date_report, "%Y/%m/%d").date()
        plant_name = unit_details.name
        unit_plans = Planning.objects.filter(plan_date__range=(from_date, to_date),
                                             unit=unit_details).order_by('plan_date')
        machines = user_based_get_machine_details(request, brand)
        plans = []
        if unit_plans:
            for machine in machines:
                if unit_plans.filter(machine=machine):
                    plans_by_machines = unit_plans
                    target_list = plans_by_machines.values_list('target', flat=True)
                    total_target = sum(target_list)
                    achieved_list = plans_by_machines.values_list('actual', flat=True)
                    total_achieved = sum(achieved_list)
                    performance = {}
                    performance["plant_name"] = str(unit_details.name+ "-" +
                                                 unit_details.code
                                                 )
                    performance["target"] = str(total_target)
                    performance["actual"] = str(total_achieved)
                    plans.append(performance)
                plans_list = json.dumps(plans)
        if not plans:
            plans_list = 'No Data'
        return render(request, 'plant_wise_report.html',
                      {'plans': plans_list,
                       'from_date': from_date_report,
                       'to_date': to_date_report,
                       'depot_code': depot_code,
                       'plant_details': plant_details,
                       'brand': brand,
                       'business_unit_details': business_unit_details})
    else:
        return render(request, 'plant_wise_report.html',
                      {'business_unit_details': business_unit_details,
                       'brand': brand})


@login_required
def bar_chart(request, brand):

    depot_code = request.GET.get('depot_code')
    machine_id = request.GET.get('machine_no')
    shift_id = request.GET.get('shift_no')
    if request.GET.get('date'):
        date = request.GET.get('date')
        try:
            plan_date = datetime.datetime.strptime(date, "%Y/%m/%d %H:%M").date()
        except:
            plan_date = datetime.datetime.strptime(date, "%Y/%m/%d").date()
    else:
        date = None
        plan_date = None
    machine_drop_down = Machine.objects.filter(planning__unit__code=depot_code,
                                               planning__plan_date=plan_date)
    shift_drop_down = Shift.objects.filter(planning__unit__code=depot_code,
                                           planning__plan_date=plan_date,
                                           planning__machine__no=machine_id)

    business_unit_details = get_business_detail(request, brand)
    try:
        if date and depot_code:
            unit_details = BusinessUnit.objects.get(id=depot_code)
            plant_name = unit_details.name
            unit_plans = Planning.objects.filter(plan_date=plan_date,
                                                 unit=unit_details,
                                                 shift__shift_no=shift_id,
                                                 machine__no=machine_id)
            all_hour = Reason.objects.filter(plan=unit_plans).order_by('created_at').values_list('time', flat=True)
            each_hour = []
            for each in all_hour:
                if each not in each_hour:
                    each_hour.append(each)
            hourly_based_data = []
            for each in each_hour:
                each_hour_report = {}
                each_hour_report["actual"] = sum(Reason.objects.filter(plan=unit_plans, time=each)
                                                 .values_list('achieved_count_per_hour', flat=True))
                each_hour_report["target"] = Reason.objects.filter(plan=unit_plans, time=each)[0].minimum_target_per_hour
                each_hour_report["machine"] = each
                hourly_based_data.append(each_hour_report)
            if not hourly_based_data:
                plans_list = 'No Data'
            else:
                plans_list = json.dumps(hourly_based_data)
            return render(request, 'hourly_report.html',
                          {'plans': plans_list,
                           'plan_date': date,
                           'brand': brand,
                           'selected_date': plan_date,
                           'depot_code': depot_code,
                           'machine_code': machine_id,
                           'shift_no': shift_id,
                           'machine_details': machine_drop_down,
                           'shift_details': shift_drop_down,
                           'plant_name': plant_name,
                           'business_unit_details': business_unit_details})
        else:
            return render(request, 'hourly_report.html',
                          {'brand': brand,
                           'business_unit_details': business_unit_details})
    except BusinessUnit.DoesNotExist:
        plans = "no data"
    context = {
        'brand': brand,
    }
    return render(request, 'hourly_report.html', context)

@login_required
def all_lines(request, brand):
    depot_code = request.GET.get('depot_code')
    business_unit_details = get_business_detail(request, brand)
    if request.GET.get('date'):
        date = request.GET.get('date')
        try:
            plan_date = datetime.datetime.strptime(date, "%Y/%m/%d %H:%M").date()
        except:
            plan_date = datetime.datetime.strptime(date, "%Y/%m/%d").date()
    else:
        date = None
        plan_date = None
    if date and depot_code:
        unit_details = BusinessUnit.objects.get(code=depot_code)
        plant_name = unit_details.name
        try:
            unit_plans = Planning.objects.filter(plan_date=plan_date, unit=unit_details)
        except:
            unit_plans = None
        plans = []
        if unit_plans:
            for each in unit_plans:
                performance = {}
                performance["machine"] = "{0} - {1} - {2} - {3}".format(each.machine.name, each.machine.no,
                                                                        each.shift.name, each.shift.shift_no,
                                                                        )
                performance["target"] = str(each.target)
                performance["actual"] = str(each.actual)
                plans.append(performance)

        plans_list = json.dumps(plans)
        if not plans:
            plans_list = 'No Data'
        return render(request, 'all-lines.html',
                      {'plans': plans_list,
                       'plan_date': date,
                       'selected_date': plan_date,
                       'depot_code': depot_code,
                       'plant_name': plant_name,
                       'brand': brand,
                       'business_unit_details': business_unit_details})
    else:
        return render(request, 'all-lines.html',
                      {'business_unit_details': business_unit_details,
                       'brand': brand
                       })


def handle_uploaded_file(uploaded_file):
    """
     This method gets the uploaded file and writes it in the upload dir under the same name
    """
    now = datetime.datetime.now()
    path = settings.UPLOAD_DIR + str(now) + uploaded_file.name
    with open(path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    return path


@login_required
def upload_machines(request, brand):
    if request.method == "POST":
        error, success = [], []
        full_path = handle_uploaded_file(request.FILES.get('machine-sheet'))
        if fnmatch.fnmatch(full_path.lower(), "*.csv"):
            with open(full_path) as csvfile:
                partreader = csv.DictReader(csvfile)
                for row_list in partreader:
                    try:
                        machine_name = row_list.get("Machine name")
                        machine_no = row_list.get("Machine No")
                        plant_code = row_list.get("Unit Code")
                        make = row_list.get("Make")
                        brand = Brand.objects.get(name=brand)
                        plant_details = BusinessUnit.objects.get(code=plant_code)
                        sel_machine = Machine.objects.filter(no=machine_no)
                        if sel_machine:
                            messages.error(request, 'Machine with this number Already exists')
                        else:
                            machine = Machine.objects.create(name=machine_name, no=machine_no,
                                                             brand=brand,
                                                             make=make, unit=plant_details)
                            success.append(str(partreader.line_num))
                    except BusinessUnit.DoesNotExist:
                        error.append(str(partreader.line_num))
        else:
            messages.error(request,
                           " Error in file format.Please, upload the CSV file.")
        if error:
            messages.error(request,
                           " Invalid data. machine numbers: {}".format(
                               ",".join(error)))
        if success:
            messages.success(request,
                             " Uploaded Machines. machine numbers: {}".format(
                                 ",".join(success)))
        return HttpResponseRedirect("/{}/machines/".format(brand))
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] \
            = 'attachment; filename="SampleMachineFile.csv"'
        writer = csv.writer(response, dialect=csv.excel)
        writer.writerow(['Machine name', 'Machine No', 'Unit Code', 'Make'])
        writer.writerow(['Machine Name', 1, 'MP001', 'SUPER MASTER'])
        return response


@login_required
def upload_plans(request, brand):
    if request.method == "POST":
        error, success = [], []
        full_path = handle_uploaded_file(request.FILES.get('plan-sheet'))
        if fnmatch.fnmatch(full_path.lower(), "*.csv"):
            with open(full_path) as csvfile:
                partreader = csv.DictReader(csvfile)
                for row_list in partreader:
                    try:
                        part_code = row_list.get("Product Code")
                        plan_date = row_list.get("Plan Date")
                        machine_no = row_list.get("Machine No")
                        plant_code = row_list.get("Unit Code")
                        shift_no = row_list.get("Shift No")
                        target = row_list.get("Target")
                        brand = Brand.objects.get(name=brand)
                        plant_details = BusinessUnit.objects.get(code=plant_code)
                        plan_date = datetime.datetime.strptime(plan_date, "%Y-%m-%d").date()

                        part_details = Product.objects.get(code=part_code)

                        machine_details = Machine.objects.get(no=machine_no)

                        shift_details = Shift.objects.get(shift_no=shift_no)
                        time_difference = get_diff_between_two_time_objects(shift_details.start, shift_details.end)
                        target_per_hour = calculate_target_per_hour(time_difference, target)
                        all_plans = Planning.objects.filter(machine=machine_details, shift=shift_details,
                                                            plan_date=plan_date,
                                                            product=part_details,)
                        sel_machine = Machine.objects.filter(unit__code=plant_code)
                        if all_plans and sel_machine:
                            messages.error(request, 'Plan Already exists')
                        else:
                            plan = Planning.objects.create(shift=shift_details, machine=machine_details,
                                                           product=part_details, brand=brand, unit=plant_details,
                                                           plan_date=plan_date, target=target,
                                                           minimum_target=target_per_hour)
                            success.append(str(partreader.line_num))
                    except (Product.DoesNotExist, Machine.DoesNotExist,
                            Shift.DoesNotExist, Brand.DoesNotExist, BusinessUnit.DoesNotExist):
                        error.append(str(partreader.line_num))
        else:
            messages.error(request,
                           " Error in file format.Please, upload the CSV file.")
        if error:
            messages.error(request,
                           " Invalid data. Plan numbers: {}".format(
                               ",".join(error)))
        if success:
            messages.success(request,
                             " Uploaded Plans. Plan numbers: {}".format(
                                 ",".join(success)))
        return HttpResponseRedirect("/{}/plan/".format(brand))
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] \
            = 'attachment; filename="SamplePlanFile.csv"'
        writer = csv.writer(response, dialect=csv.excel)
        writer.writerow(['SI No', 'Shift No',
                         'Machine No', 'Product Code',
                         'Plan Date', 'Unit Code', 'Target'])
        writer.writerow([1, 1, 1, 'CR001', '2017-08-22', 'MP001', '50000'])
        return response


@login_required
def upload_shift(request, brand):
    if request.method == "POST":
        error, success = [], []
        full_path = handle_uploaded_file(request.FILES.get('shift-sheet'))
        if fnmatch.fnmatch(full_path.lower(), "*.csv"):
            with open(full_path) as csvfile:
                partreader = csv.DictReader(csvfile)
                for row_list in partreader:
                    try:
                        shift_name = row_list.get("Shift Name")
                        shift_number = row_list.get("Shift Number")
                        start_time = row_list.get("Start Time")
                        end_time = row_list.get("End Time")
                        brand = Brand.objects.get(name=brand)
                        shift = Shift.objects.create(name=shift_name, shift_no=shift_number,
                                                     start=start_time, brand=brand, end=end_time,
                                                     )
                        success.append(str(partreader.line_num))
                    except:
                        error.append(str(partreader.line_num))
        else:
            messages.error(request,
                           " Error in file format.Please, upload the CSV file.")
        if error:
            messages.error(request,
                           " Invalid data. Shift numbers: {}".format(
                               ",".join(error)))
        if success:
            messages.success(request,
                             " Uploaded Shifts. Shift numbers: {}".format(
                                 ",".join(success)))
        return HttpResponseRedirect("/{}/shifts/".format(brand))
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] \
            = 'attachment; filename="SampleShiftFile.csv"'
        writer = csv.writer(response, dialect=csv.excel)
        writer.writerow(['Shift Name', 'Shift Number', 'Start Time', 'End Time'])
        writer.writerow(['name', 1, '09:00:00', '17:00:00'])
        return response


@login_required
def upload_business_unit(request, brand):
    if request.method == "POST":
        error, success = [], []
        full_path = handle_uploaded_file(request.FILES.get('unit-details-sheet'))
        if fnmatch.fnmatch(full_path.lower(), "*.csv"):
            with open(full_path) as csvfile:
                partreader = csv.DictReader(csvfile)
                for row_list in partreader:
                    try:
                        if row_list.get("Unit Code"):
                            plant_name = row_list.get("Unit Name")
                            address = row_list.get("Address")
                            plant_code = row_list.get("Unit Code")
                            brand = Brand.objects.get(name=brand)
                            # plant_type = row_list.get("Unit Type")

                            # type = constants.bussiness_unit_type[plant_type]
                            product = BusinessUnit.objects.create(name=plant_name, code=plant_code,
                                                                  address=address, brand=brand)
                            success.append(str(partreader.line_num))
                        else:
                            error.append(str(partreader.line_num))
                    except KeyError as ex:
                        error.append(str(partreader.line_num))
                    except IntegrityError as ex:
                        error.append(str(partreader.line_num))
        else:
            messages.error(request,
                           " Error in file format.Please, upload the CSV file.")
        if error:
            messages.error(request,
                           " Invalid data. Business Unit Number: {}".format(
                               ",".join(error)))
        if success:
            messages.success(request,
                             " Uploaded Units. Business Unit Number: {}".format(
                                 ",".join(success)))
        return HttpResponseRedirect("/{}/business-unit/".format(brand))
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] \
            = 'attachment; filename="SampleUnitDetailsUploadFile.csv"'
        writer = csv.writer(response, dialect=csv.excel)
        writer.writerow(['Unit Name', 'Address', 'Unit Code'])
        writer.writerow(['Gladminds', 'Bangalore,India', 'MP005'])
        return response


@login_required
def upload_categories(request, brand):
    if request.method == "POST":
        error, success = [], []
        full_path = handle_uploaded_file(request.FILES.get('category-sheet'))
        if fnmatch.fnmatch(full_path.lower(), "*.csv"):
            with open(full_path) as csvfile:
                partreader = csv.DictReader(csvfile)
                for row_list in partreader:
                    try:
                        category_name = row_list.get("Category Name")
                        category_code = row_list.get("Category Code")
                        brand = Brand.objects.get(name=brand)
                        product = Category.objects.create(name=category_name, code=category_code,
                                                          brand=brand)
                        success.append(str(partreader.line_num))
                    except IntegrityError as ex:
                        error.append(str(partreader.line_num))
        else:
            messages.error(request,
                           " Error in file format.Please, upload the CSV file.")
        if error:
            messages.error(request,
                           " Invalid data. Category Number: {}".format(
                               ",".join(error)))
        if success:
            messages.success(request,
                             " Uploaded Categories. Category Number: {}".format(
                                 ",".join(success)))
        return HttpResponseRedirect("/{}/categories/".format(brand))
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] \
            = 'attachment; filename="SampleCategoryFile.csv"'
        writer = csv.writer(response, dialect=csv.excel)
        writer.writerow(['Category Name', 'Category Code'])
        writer.writerow(['Cartoons', 'CT002'])
        return response


@login_required
def upload_products(request, brand):
    if request.method == "POST":
        error, success = [], []
        full_path = handle_uploaded_file(request.FILES.get('products-sheet'))
        if fnmatch.fnmatch(full_path.lower(), "*.csv"):
            with open(full_path) as csvfile:
                partreader = csv.DictReader(csvfile)
                for row_list in partreader:
                    try:
                        part_code = row_list.get("Product Code")
                        product_name = row_list.get("Product Name")
                        product_description = row_list.get("Product Description")
                        category_code = row_list.get("Category Code")
                        brand = Brand.objects.get(name=brand)
                        category = Category.objects.get(code=category_code)
                        product = Product.objects.create(name=product_name, code=part_code,
                                                         description=product_description, brand=brand,
                                                         category=category)
                        success.append(str(partreader.line_num))
                    except Category.DoesNotExist:
                        error.append(str(partreader.line_num))
                    except IntegrityError as ex:
                        error.append(str(partreader.line_num))
        else:
            messages.error(request,
                           " Error in file format.Please, upload the CSV file.")
        if error:
            messages.error(request,
                           " Invalid data. Product number: {}".format(
                               ",".join(error)))
        if success:
            messages.success(request,
                             " Uploaded Products. Product numbers: {}".format(
                                 ",".join(success)))
        return HttpResponseRedirect("/{}/products/".format(brand))
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] \
            = 'attachment; filename="SampleProductFile.csv"'
        writer = csv.writer(response, dialect=csv.excel)
        writer.writerow(['Product Name', 'Product Description', 'Product Code', 'Category Code'])
        writer.writerow(['Cars', 'BMW Cars', 'CR001', 'CT001'])
        return response


def upload_product_stocks(request, brand=None):
    if request.method == "POST":
        error, success = [], []
        full_path = handle_uploaded_file(request.FILES.get('stocks-sheet'))
        if fnmatch.fnmatch(full_path.lower(), "*.csv"):
            with open(full_path) as csvfile:
                partreader = csv.DictReader(csvfile)
                for row_list in partreader:
                    try:
                        product_code = row_list.get("Product Code")
                        product = Product.objects.get(code=product_code)
                        new_stocks = row_list.get("Available Quantity")
                        brand = Brand.objects.get(name=brand)
                        try:
                            stocks = Stocks.objects.get(product=product, brand=brand)
                        except Stocks.DoesNotExist:
                            stocks = Stocks.objects.create(product=product, brand=brand)
                        stocks.available_stocks = int(stocks.available_stocks) + int(new_stocks)
                        stocks.save()
                        success.append(str(partreader.line_num))
                    except Stocks.DoesNotExist:
                        error.append(str(partreader.line_num))
                    except Product.DoesNotExist:
                        error.append(str(partreader.line_num))
        else:
            messages.error(request,
                           " Error in file format.Please, upload the CSV file.")
        if error:
            messages.error(request,
                           " Invalid data. Product number: {}".format(
                               ",".join(error)))
        if success:
            messages.success(request,
                             " Uploaded Stocks.: {}".format(
                                 ",".join(success)))
        return HttpResponseRedirect("/{}/products/".format(brand))
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] \
            = 'attachment; filename="SampleStockFile.csv"'
        writer = csv.writer(response, dialect=csv.excel)
        writer.writerow(['Product Code', 'Available Quantity'])
        writer.writerow(['P111', '1000'])
        return response


def get_diff_between_two_time_objects(start_time, end_time):
    dummydate = datetime.date(2000, 1, 1)  # Needed to convert time to a datetime object
    dt1 = datetime.datetime.combine(dummydate, start_time)
    dt2 = datetime.datetime.combine(dummydate, end_time)
    diffrence = dt2 - dt1
    return diffrence


def calculate_target_per_hour(time_difference, target):
    total_working_hour = time_difference.seconds/60/60
    total_working_hour = int(target)/int(total_working_hour)
    return total_working_hour

#
# def get_time_interval(start_hour, end_hour):
#     today = datetime.datetime.now()
#     now_time = today.hour
#     counter = 0
#     for i in range(start_hour, end_hour):
#         if now_time == i:
#             counter
#             break
#         else:
#             counter = counter+1
#     return counter


def get_time_interval(start_hour, end_hour):
    today = datetime.datetime.now()
    if start_hour < end_hour:
        dt2 = datetime.datetime.combine(today.date(), end_hour)
    else:
        end_day = today + relativedelta(months=0, day=today.date().day + 1, hour=0, minute=0, microsecond=0)
        dt2 = datetime.datetime.combine(end_day.date(), end_hour)
    diffrence = dt2 - today
    counter = diffrence.seconds / 60 / 60
    return counter

#
# def scanned_product_count(today, plan, timer):
#     list_temp, time = [], []
#     from_time = plan.shift.start.hour
#     end_time = plan.shift.start.hour+timer+2
#     shift_end_time = plan.shift.end.hour
#     for i in range(from_time, end_time):
#         count_and_time = {}
#         time_dict = {}
#         start_time = today+relativedelta(months=0, day=0, hour=i, minute=0, second=0, microsecond=0)
#         end_time = today+relativedelta(months=0, day=0, hour=i+1, minute=0, second=0, microsecond=0)
#         count = ProductCount.objects.filter(
#             created_at__range=(start_time, end_time),
#             plan_details=plan
#         ).count()
#         time_dict["start_time"] = i
#         time_dict["end_time"] = i+1
#         if i < shift_end_time:
#             count_and_time["scanner_count"] = count
#         else:
#             count_and_time["scanner_count"] = "No Live Process"
#         list_temp.append(count_and_time)
#         time.append(time_dict)
#     return list_temp, time


def scanned_product_count(today, plan):
    list_temp, time = [], []
    start_plant = datetime.datetime.combine(today.date(), plan.shift.start)
    if plan.shift.start.hour < plan.shift.end.hour:
        end_plan = datetime.datetime.combine(today.date(), plan.shift.end)
    else:
        end_day = today + relativedelta(months=0, day=today.date().day + 1, hour=0, minute=0, microsecond=0)
        end_plan = datetime.datetime.combine(end_day.date(), plan.shift.end)
    diffrence = end_plan - today
    past_hour = today.time().hour - 1
    if past_hour == -1:
        past_hour = 0
    next_hour = today.time().hour + 1
    if next_hour == 24:
        next_hour = 0
    for i in [past_hour, today.time().hour, next_hour]:
        count_and_time = {}
        time_dict = {}
        start_time = today + relativedelta(months=0, day=0, hour=i, minute=0, second=0, microsecond=0)
        try:
            end_time = today + relativedelta(months=0, day=0, hour=i + 1, minute=0, second=0, microsecond=0)
        except:
            if i == 23:
                end_time = today + relativedelta(months=0, day=0, hour=0, minute=0, second=0, microsecond=0)
            else:
                end_time = today + relativedelta(months=0, day=0, hour= i + 1, minute=0, second=0, microsecond=0)
        count = ProductCount.objects.filter(
            created_at__range=(start_time, end_time), plan_details=plan
        ).values_list('count', flat=True)
        if count:
            count = sum(count)
        else:
            count = 0
        time_dict["start_time"] = i
        if i + 1 == 24:
            time_dict["end_time"] = 0
        else:
            time_dict["end_time"] = i + 1
        if i < plan.shift.end.hour:
            count_and_time["scanner_count"] = count
        else:
            count_and_time["scanner_count"] = "No Live Process"
        list_temp.append(count_and_time)
        time.append(time_dict)
    return list_temp, time


@login_required
def performance(request, brand):
    today = datetime.datetime.now()
    # date = today.date()
    if request.GET.get('date'):
        date = datetime.datetime.strptime(request.GET.get('date'), "%Y/%m/%d %H:%M").date()
        bar_code_date = datetime.datetime.strftime(date, "%Y/%m/%d")
    else:
        date = None
    if request.user.user_brand.group.name == 'PlantAdmin':
        depot_code = BusinessUnit.objects.filter(id__in=request.user.user_brand.unit.all())
    elif request.user.user_brand.group.name == 'SuperVisor':
        depot_code = BusinessUnit.objects.filter(id=request.user.user_brand.unit.all()[0].id)
    else:
        depot_code = request.GET.get('depot_code')
    drop_down_details = get_business_detail(request, brand)
    if date and depot_code:
        unit_details = BusinessUnit.objects.get(code=depot_code)
        plan_date = date
        plans = Planning.objects.filter(plan_date=plan_date,
                                        unit=unit_details)
        plant_perfomance =[]
        for plan in plans:
            plan_detailes_dict = {}
            time_difference = get_diff_between_two_time_objects(plan.shift.start, plan.shift.end)
            target_per_hour = calculate_target_per_hour(time_difference, plan.target)
            # target_per_hour = plan.minimum_target
            timer = get_time_interval(plan.shift.start, plan.shift.end)
            plan_detailes_dict["plant"] = plan
            scanned_parts_count, time = scanned_product_count(today, plan)
            plan_detailes_dict["target_per_hour"] = target_per_hour
            plan_detailes_dict["scanned_parts_count"] = scanned_parts_count[-3:]
            plant_perfomance.append(plan_detailes_dict)
        if not plans:
            plant_perfomance = 'No Data'
            return render(request, 'performance-calculation.html',
                          {'plans': plant_perfomance,
                           'plan_date': date,
                           'brand': brand,
                           'plant_details': unit_details,
                           'bar_code_date': bar_code_date,
                           'depot_code': depot_code,
                           'business_unit_details': drop_down_details})
        return render(request, 'performance-calculation.html',
                      {'plans': plant_perfomance,
                       'brand': brand,
                       'plan_date': date,
                       'times': time[-3:],
                       'plant_details': unit_details,
                       'bar_code_date': bar_code_date,
                       'depot_code': depot_code,
                       'business_unit_details': drop_down_details})
    else:
        return render(request, 'performance-calculation.html',
                      {'business_unit_details': drop_down_details,
                       'brand': brand})


@login_required
def business_unit(request, brand=None):
    page = request.GET.get('page')
    query = request.GET.get('q')
    business_unit_details = get_business_detail(request, brand)
    try:
        if query:
            search_query = Q(name__icontains=query) | Q(code__icontains=query)
            business_unit_details = business_unit_details.filter(search_query)
        business_unit_details, pagination_info = get_paginated_objects(business_unit_details, page, 10)
    except BusinessUnit.DoesNotExist:
        pass
    return render(request, 'business-unit.html',
                  {'brand': brand,
                   'business_unit_details': business_unit_details, 'pagination_info': pagination_info}, )


@login_required
def products(request, brand=None):
    page = request.GET.get('page')
    query = request.GET.get('q')
    products_details = Product.objects.filter(brand__name=brand).order_by('-id')
    if query:
        search_query = Q(name__icontains=query) | Q(code__icontains=query) | \
                       Q(description__icontains=query)
        products_details = products_details.filter(search_query)
    products_details, pagination_info = get_paginated_objects(products_details, page, 10)
    return render(request, 'products.html',
                  {'brand': brand,
                   'products_details': products_details, 'pagination_info': pagination_info}, )


@login_required
def machines(request, brand=None):
    page = request.GET.get('page')
    query = request.GET.get('q')
    machine_details = user_based_get_machine_details(request, brand)
    if query:
        search_query = Q(name__icontains=query) | Q(no__icontains=query) | \
                       Q(unit__name__icontains=query) | Q(unit__code__icontains=query)
        machine_details = machine_details.filter(search_query)
    machine_details, pagination_info = get_paginated_objects(machine_details, page, 10)
    return render(request, 'machines.html',
                  {'brand': brand,
                   'machine_details': machine_details, 'pagination_info': pagination_info}, )


@login_required
def categories(request, brand=None):
    page = request.GET.get('page')
    query = request.GET.get('q')
    category_details = Category.objects.filter(brand__name=brand).order_by('-id')
    if query:
        search_query = Q(name__icontains=query) | Q(code__icontains=query)
        category_details = category_details.filter(search_query)
    category_details, pagination_info = get_paginated_objects(category_details, page, 10)
    return render(request, 'categories.html',
                  {'brand': brand,
                   'category_details': category_details, 'pagination_info': pagination_info}, )


@login_required
def shifts(request, brand):
    page = request.GET.get('page')
    query = request.GET.get('q')
    shift_details = Shift.objects.filter(brand__name=brand).order_by('-id')
    if query:
        search_query = Q(name__icontains=query) | Q(shift_no__icontains=query)
        shift_details = shift_details.filter(search_query)
    shift_details, pagination_info = get_paginated_objects(shift_details, page, 10)
    return render(request, 'shifts.html',
                  {'brand': brand,
                   'shift_details': shift_details, 'pagination_info': pagination_info}, )


@login_required
def download_products(request, brand):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] \
        = 'attachment; filename="ProductStocksFile.csv"'
    writer = csv.writer(response, dialect=csv.excel)
    products = Product.objects.filter(brand__name=brand).order_by('-id')
    writer.writerow(['Product Name', 'Product Code', 'Product Description', 'Category Code', 'Category Name', 'Available Stocks'])
    for product in products:
        row_list = []
        row_list.append((product.name).replace(u'\xa0', ' '))
        row_list.append((product.code).replace(u'\xa0', ' '))
        row_list.append((product.description).replace(u'\xa0', ' '))
        row_list.append((product.category.code).replace(u'\xa0', ' '))
        row_list.append((product.category.name).replace(u'\xa0', ' '))
        row_list.append(product.get_total_stocks())
        writer.writerow(row_list)
    return response


@login_required
def download_issued_stocks(request, brand):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] \
        = 'attachment; filename="IssuedProductDetails.csv"'
    writer = csv.writer(response, dialect=csv.excel)
    products = IssuedStocks.objects.filter(brand__name=brand).order_by('-id')
    writer.writerow(['Product Name', 'Product Code', 'Product Description', 'Issued Stocks', 'Issued Date', 'Remarks'])
    for product in products:
        row_list = []
        row_list.append(product.product.name)
        row_list.append(product.product.code)
        row_list.append(product.product.description)
        row_list.append(product.issued_stocks)
        row_list.append("{0} {1}:{2}".format(str(product.created_at.date()),
                                             str(product.created_at.time().hour), str(product.created_at.time().minute)))
        row_list.append(product.remarks)
        writer.writerow(row_list)
    return response


@login_required
def issued_stocks(request, brand):
    page = request.GET.get('page')
    query = request.GET.get('q')
    stock_details = IssuedStocks.objects.filter(brand__name=brand).order_by('-id')
    if query:
        search_query = Q(product__name__icontains=query) | Q(product__code__icontains=query)
        stock_details = stock_details.filter(search_query)
    stock_details, pagination_info = get_paginated_objects(stock_details, page, 10)
    return render(request, 'issued_stocks.html',
                  {'brand': brand,
                   'stock_details': stock_details, 'pagination_info': pagination_info}, )


@login_required
def user_details(request, brand):

    page = request.GET.get('page')
    query = request.GET.get('q')
    user_details = UserBrand.objects.filter(brand__name=brand)\
        .exclude(user__is_superuser=True).order_by('-id')
    if query:
        search_query = Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query) | \
                       Q(user__username__icontains=query) | Q(group__name__icontains=query) | \
                       Q(unit__name__icontains=query) | Q(unit__code__icontains=query)
        user_details = user_details.filter(search_query)
    user_details, pagination_info = get_paginated_objects(user_details, page, 10)
    return render(request, 'user-details.html',
                  {'brand': brand,
                   'user_details': user_details, 'pagination_info': pagination_info}, )


@login_required
def issue_product(request, productcode=None, brand=None):
    if request.method == "POST":
        try:
            product = Product.objects.get(code=str(request.POST.get('productcode')))
            issued_count = int(request.POST.get('issue_product'))
            remarks = str(request.POST.get('remarks'))
            stocks = Stocks.objects.get(product=product)
            if stocks.available_stocks > 0:
                if stocks.available_stocks >= issued_count:
                    stocks.available_stocks = stocks.available_stocks - issued_count
                    stocks.save()
                    brand = Brand.objects.get(name=brand)
                    IssuedStocks.objects.create(product=product, issued_stocks=issued_count,
                                                remarks=remarks,
                                                issued_by=request.user.user_brand,
                                                brand=brand)
                    message = " {0} is updated successfully.".format(productcode)
        except:
            message = " {0} is not able update.".format(productcode)
        page = request.GET.get('page')
        stock_details = IssuedStocks.objects.filter(brand__name=brand).order_by('-id')
        stock_details, pagination_info = get_paginated_objects(stock_details, page, 10)
        return render(request, 'issued_stocks.html',
                      {'brand': brand,
                       'stock_details': stock_details, 'message': message, 'pagination_info': pagination_info}, )
    else:
        product_details = Product.objects.get(code=productcode)
        return render(request, 'issue-products.html',
                      {'brand': brand, 'product_details': product_details}, )


def get_machine_details(request, brand):
    resp, success, machine_items = {}, False, []
    depot_code = request.GET.get("depot_code")
    try:
        machine = Machine.objects.filter(unit__id=depot_code)
        for i in machine:
            temp_dict = {}
            temp_dict["name"] = i.name
            temp_dict["no"] = i.no
            temp_dict["id"] = i.id
            machine_items.append(temp_dict)
        success = True
    except Machine.DoesNotExist:
        success = False
    resp["success"] = success
    resp["machine_items"] = machine_items
    return JsonResponse(resp)


def get_plant_details(request, brand):
    resp, success, plant_items = {}, False, []
    depot_code = request.GET.get("depot_code")
    try:
        plant = BusinessUnit.objects.filter(code=depot_code,)
        for i in plant:
            temp_dict = {}
            temp_dict["name"] = i.name
            temp_dict["no"] = i.code
            plant_items.append(temp_dict)
        success = True
    except BusinessUnit.DoesNotExist:
        success = False
    resp["success"] = success
    resp["plant_items"] = plant_items
    return JsonResponse(resp)


def check_username(request, brand):
    resp, success, machine_items = {}, False, []
    username = request.GET.get("username")
    try:
        User.objects.get(username=username)
        success = False
    except User.DoesNotExist:
        success = True
    resp["success"] = success
    return JsonResponse(resp)


@login_required
def email_log(request, brand=None):
    page = request.GET.get('page')
    query = request.GET.get('q')
    email_log = EmailLog.objects.filter(brand__name=brand).order_by('-created_at')
    if query:
        search_query = Q(sender__icontains=query) | Q(receiver__icontains=query) | Q(cc__icontains=query)
        email_log = email_log.filter(search_query)
    email_log, pagination_info = get_paginated_objects(email_log, page, 10)
    return render(request, 'email_log.html',
                  {'brand': brand, 'email_log': email_log,
                   'pagination_info': pagination_info})


@login_required
def logout(request):
    """
    Removes the authenticated user's ID from the request and flushes their
    session data.
    """
    auth_logout(request)
    request.session.flush()
    if request.GET.get('next'):
        return HttpResponseRedirect(request.GET['next'])
    return HttpResponseRedirect('/')


def get_paginated_objects(objects, page, obj_per_page):
    paginator = Paginator(objects, obj_per_page)
    if page:
        page = page
    else:
        page = 1
    page_number = paginator.page(int(page))
    count = page_number.object_list.count()
    try:
        paginated_objects = paginator.page(page)
        if paginated_objects.has_next():
            count = count * int(page)
        else:
            count = paginator.object_list.count()
    except PageNotAnInteger:
        paginated_objects = paginator.page(1)
    except EmptyPage:
        paginated_objects = paginator.page(paginator.num_pages)
    pagination_info = {
        'has_previous': paginated_objects.has_previous,
        'previous_page_number': paginated_objects.previous_page_number,
        'number': paginated_objects.number,
        'num_pages': paginated_objects.paginator.num_pages,
        'has_next': paginated_objects.has_next,
        'next_page_number': paginated_objects.next_page_number,
        'page_range': paginated_objects.paginator.page_range,
        'count_per_page': count,
        'has_other_pages': paginated_objects.has_other_pages(),
        'total_count': paginator.object_list.count()
    }
    return paginated_objects, pagination_info


def email_html(subject="Email Template", to=('gm.glads@gmail.com', ), bcc=('gm.glads@gmail.com', ),
               from_email=settings.EMAIL_HOST_USER, email_template='', ctx=None):
    if ctx is None:
        ctx = {'username': 'Patron'}
    message = get_template(email_template).render(Context(ctx))
    msg = EmailMessage(subject, message, to=to, bcc=bcc, from_email=from_email)
    msg.content_subtype = 'html'
    # msg.send()
    body = "Dear {0},\n\nPlease click the below link for reset the password.\n\n" \
           "{1}\n\n" \
           "Regards,\n" \
           "Gladminds".format(ctx['username'], ctx['verification_link'])
    toaddr = to
    fromaddr = from_email
    message_subject = subject
    message_text = body
    message = "From: %s\r\n" % fromaddr \
              + "To: %s\r\n" % toaddr \
              + "Subject: %s\r\n" % message_subject \
              + "\r\n" \
              + message_text
    toaddrs = [toaddr]
    server = smtplib.SMTP(settings.EMAIL_HOST)
    server.starttls()
    server.set_debuglevel(1)
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.sendmail(fromaddr, toaddrs, message)
    server.quit()
    return 'success'


def forgot_password(request):
    form = ForgotPasswordForm()
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = UserBrand.objects.get(user__email=email.lower())

                email_token_obj = EmailVerificationToken.objects.filter(user=user,
                                                                        valid_till__gt=datetime.datetime.now(),
                                                                        verified=False).first()

                if email_token_obj is None:
                    token = str(uuid.uuid4())
                    email_token_obj = EmailVerificationToken.objects.create(
                        user=user,
                        token=token,
                        valid_till=datetime.datetime.now() + datetime.timedelta(hours=24),
                        type='1',
                    )
                else:
                    token = email_token_obj.token

                protocol = 'https://' if request.is_secure() else 'http://'
                email_html(
                    subject="Reset your password",
                    to=(user.user.email,),
                    email_template='reset-password.html',
                    ctx={
                        'username': user.user.first_name + " " + user.user.last_name,
                        'verification_link':  protocol + request.META['HTTP_HOST'] + reverse(
                            'reset_password', kwargs={'token': token}
                        ),
                    }
                )
                return render(request, 'forgot-password-submitted.html', locals())
            except User.DoesNotExist:
                return render(request, 'forgot-password.html', locals())
    return render(request, 'forgot-password.html', locals())


def reset_password(request, token=None):
    email_token_obj = EmailVerificationToken.objects.filter(token=token, valid_till__gt=datetime.datetime.now(),
                                                            verified=False).first()
    if email_token_obj is not None:
        form = ResetPasswordForm()
        if request.method == 'POST':
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                password = form.cleaned_data['password']
                user = email_token_obj.user
                user.user.set_password(password)
                user.user.save()
                email_token_obj.verified = True
                email_token_obj.save()
                return render(request, 'reset-password-success.html', locals())
    else:
        return render(request, 'reset-password-expired.html', locals())
    return render(request, 'reset-password.html', locals())


def add_category(request, brand=None):
    category_form = CategoryForm()
    if request.method == 'POST':
        category_form = CategoryForm(request.POST)
        if category_form.is_valid():
            name = category_form.cleaned_data.get('name')
            code = category_form.cleaned_data.get('code')
            brand = Brand.objects.get(name=brand)
            Category.objects.create(name=name, code=code, brand=brand)
            messages.success(
                request, "{} Category Added Successfully".format(name)
            )
            return redirect("/{}/categories/".format(brand))
    return render(request, 'add_category.html', locals())


def add_business_unit(request, brand=None):
    business_unit_form = BusinessUnitForm()
    if request.method == 'POST':
        business_unit_form = BusinessUnitForm(request.POST)
        if business_unit_form.is_valid():
            name = business_unit_form.cleaned_data.get('name')
            address = business_unit_form.cleaned_data.get('address')
            code = business_unit_form.cleaned_data.get('code')
            # plant_type = business_unit_form.cleaned_data.get('type')
            # try:
            #     type = constants.plant_type[plant_type]
            # except:
            #     messages.success(
            #         request, "{} Not Able to Added".format(name)
            #     )
            #     return redirect('/business-unit/')
            brand = Brand.objects.get(name=brand)
            BusinessUnit.objects.create(name=name, code=code, brand=brand,
                                        address=address)
            messages.success(
                request, "{} Plant Added Successfully".format(name)
            )
            return redirect("/{}/business-unit/".format(brand))
    return render(request, 'add_business_unit.html', locals())


def add_machine(request, brand=None):
    user = request.user
    machine_form = MachineForm(user)
    if request.method == 'POST':
        machine_form = MachineForm(user, request.POST)
        if machine_form.is_valid():
            name = machine_form.cleaned_data.get('name')
            no = machine_form.cleaned_data.get('no')
            make = machine_form.cleaned_data.get('make')
            unit = machine_form.cleaned_data.get('unit')
            brand = Brand.objects.get(name=brand)
            Machine.objects.create(name=name, no=no, brand=brand,
                                   make=make, unit=unit)
            messages.success(
                request, "{} Machine Added Successfully".format(name)
            )
            return redirect("/{}/machines/".format(brand))
    return render(request, 'add_machine.html', locals())


def add_shift(request, brand=None):
    shift_form = ShiftForm()
    if request.method == 'POST':
        shift_form = ShiftForm(request.POST)
        if shift_form.is_valid():
            name = shift_form.cleaned_data.get('name')
            shift_no = shift_form.cleaned_data.get('shift_no')
            start = shift_form.cleaned_data.get('start')
            end = shift_form.cleaned_data.get('end')
            brand = Brand.objects.get(name=brand)
            Shift.objects.create(name=name, shift_no=shift_no, brand=brand,
                                 start=start, end=end)
            messages.success(
                request, "{} Shift Added Successfully".format(name)
            )
            return redirect("/{}/shifts/".format(brand))
    return render(request, 'add_shift.html', locals())


def add_product(request, brand=None):
    user = request.user
    product_form = ProductForm(user)
    if request.method == 'POST':
        product_form = ProductForm(user, request.POST)
        if product_form.is_valid():
            name = product_form.cleaned_data.get('name')
            code = product_form.cleaned_data.get('code')
            description = product_form.cleaned_data.get('description')
            category = product_form.cleaned_data.get('category')
            brand = Brand.objects.get(name=brand)
            Product.objects.create(name=name, code=code, brand=brand,
                                   category=category, description=description)
            messages.success(
                request, "{} Product Added Successfully".format(name)
            )
            return redirect("/{}/products/".format(brand))
    return render(request, 'add_product.html', locals())


def add_plan(request, brand):
    user = request.user
    planning_form = PlanningForm(user)
    if request.method == 'POST':
        planning_form = PlanningForm(user, request.POST)
        if planning_form.is_valid():
            product = planning_form.cleaned_data.get('product')
            shift = planning_form.cleaned_data.get('shift')
            machine = planning_form.cleaned_data.get('machine')
            target = planning_form.cleaned_data.get('target')
            plan_date = planning_form.cleaned_data.get('plan_date')
            unit = planning_form.cleaned_data.get('unit')
            time_difference = get_diff_between_two_time_objects(shift.start, shift.end)
            target_per_hour = calculate_target_per_hour(time_difference, target)
            brand = Brand.objects.get(name=brand)
            all_plans = Planning.objects.filter(machine=machine, shift=shift, plan_date=plan_date,
                                                product=product)
            Planning.objects.create(shift=shift, product=product, brand=brand, unit=unit, machine=machine,
                                    target=target, plan_date=plan_date, minimum_target=target_per_hour)
            messages.success(
                request, "{} Plan Added Successfully".format(plan_date)
            )
            return redirect("/{}/plan/".format(brand))
    return render(request, 'add_planning.html', locals())
#
# if all_plans:
#     messages.success(
#         request, "{} Plan Already exists".format(plan_date)
#     )
#     return redirect("/{}/add-plan/".format(brand))
# else:
#
@login_required
@transaction.atomic
def add_user(request, brand):
    user = request.user
    userbrand_form = UserBrandForm(user)
    if request.method == 'POST':
        userbrand_form = UserBrandForm(user, request.POST)
        if userbrand_form.is_valid():
            profile_image = request.FILES.get('image_url')
            first_name = userbrand_form.cleaned_data.get('first_name')
            last_name = userbrand_form.cleaned_data.get('last_name')
            machine = userbrand_form.cleaned_data.get('machine')
            group = userbrand_form.cleaned_data.get('group')
            mobile_number = userbrand_form.cleaned_data.get('mobile_number')
            unit = userbrand_form.cleaned_data.get('unit')
            email = userbrand_form.cleaned_data.get('email')
            brand = Brand.objects.get(name=brand)
            user = User()
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = email
            user.save()
            user.set_password(mobile_number)
            user.save()

            user_brand = UserBrand()
            user_brand.image_url = profile_image
            user_brand.brand = brand
            user_brand.user = user
            user_brand.group = group
            user_brand.image_url = profile_image
            user_brand.mobile_number = mobile_number
            user_brand.save()

            user_brand.unit = unit
            user_brand.machine = machine
            user_brand.save()

            messages.success(
                request, "{} Added Successfully".format(first_name)
            )

            return redirect('/{}/user-details/'.format(brand))
    return render(request, 'add_user.html', locals())


@login_required
def edit_user_details(request, user_id=None, brand=None):
    user_details = UserBrand.objects.get(user__id=user_id)
    user = request.user
    userbrand_form = UserBrandForm(user, initial={
        'first_name': user_details.user.first_name,
        'last_name': user_details.user.last_name,
        'email': user_details.user.email,
        'mobile_number': user_details.mobile_number,
        'group': user_details.group,
        'unit': user_details.unit.all(),
        'image_url': user_details.image_url.url if user_details.image_url else None,
        'machine': user_details.machine.all(),
    })
    image_url = user_details.image_url.url if user_details.image_url else None
    machine_details = Machine.objects.filter(brand__name=brand)
    user_machines = user_details.machine.all()
    form_update = True
    if request.method == 'POST':
        userbrand_form = UserBrandForm(user, request.POST)
        if userbrand_form.is_valid():
            profile_image = request.FILES.get('image_url')
            first_name = userbrand_form.cleaned_data.get('first_name')
            last_name = userbrand_form.cleaned_data.get('last_name')
            machine = userbrand_form.cleaned_data.get('machine')
            group = userbrand_form.cleaned_data.get('group')
            mobile_number = userbrand_form.cleaned_data.get('mobile_number')
            unit = userbrand_form.cleaned_data.get('unit')
            email = userbrand_form.cleaned_data.get('email')
            brand = Brand.objects.get(name=brand)
            user = User.objects.get(id=user_id)
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = email
            user.set_password(mobile_number)

            user_brand = UserBrand.objects.get(user__id=user_id)
            user_brand.image_url = profile_image
            user_brand.brand = brand
            user_brand.user = user
            user_brand.group = group
            user_brand.image_url = profile_image
            user_brand.mobile_number = mobile_number
            user_brand.unit = unit
            user_brand.machine = machine
            user.save()
            user_brand.save()
            messages.success(
                request, "{} Updated Successfully".format(first_name)
            )
            return redirect("/{}/user-details/".format(brand), locals())
    return render(request, 'add_user.html', locals())


# def production_count_not_updated_mail(planning):
#     plant_admin_mail_id = UserBrand.objects.filter(group__name='PlantAdmin',
#                                                    unit=planning.unit).values_list('user__email', flat=True)
#     cc_email = UserBrand.objects.filter((Q(group__name='SuperVisor') & Q(machine=planning.machine)) |
#                                         Q(group__name='Admin')
#                                         )
#     cc_email_list = []
#     for each in cc_email:
#         cc_email_list.append(each.user.email)
#     receiver = plant_admin_mail_id
#     sender = 'Gladminds'
#     subject = 'Production count not updated {0} at {1} on {2}'.format(planning.machine.name,
#                                                   planning.unit.name,
#                                                   planning.plan_date,planning
#                                                                               )
#     body = "Dear Team,\n\n" \
#            "Failed to update the count." \
#            "Machine: {1} - {2}\n" \
#            "Shift: {5}\n" \
#            "Plat: {6} - {7}\n" \
#            "Time: {8}\n" \
#            "Regards,\n" \
#            "Gladminds".format(planning.machine.no, planning.machine.name,
#                               planning.shift.shift_no,
#                               planning.unit.code, planning.unit.name, datetime.datetime.now(),
#                               )
#     try:
#         toaddr = receiver
#         cc = cc_email_list
#         fromaddr = sender
#         message_subject = subject
#         message_text = body
#         message = "From: %s\r\n" % fromaddr \
#                   + "To: %s\r\n" % toaddr \
#                   + "CC: %s\r\n" % ",".join(cc) \
#                   + "Subject: %s\r\n" % message_subject \
#                   + "\r\n" \
#                   + message_text
#         toaddrs = [toaddr] + cc
#         server = smtplib.SMTP(settings.EMAIL_HOST)
#         server.starttls()
#         server.set_debuglevel(1)
#         server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
#         server.sendmail(fromaddr, toaddrs, message)
#         server.quit()
#         EmailLog.objects.create(subject=subject, message=message, sender=sender, receiver=receiver, cc=cc)
#         return True
#     except Exception as ex:
#         return False


# def stocks_created(request, brand):
#     import ipdb; ipdb.set_trace()
#     brand = Brand.objects.get(name=brand)
#     current_date = datetime.datetime.now()
#     current_hour = strftime("%Y-%m-%d %H")
#     last_range = datetime.datetime.strptime(current_hour, '%Y-%m-%d %H')
#     first_range = last_range - datetime.timedelta(minutes=60)
#     depot_code = request.GET.get('depot_code')
#     unitcode = []
#     unit_details = BusinessUnit.objects.all()
#     for unit_detail in unit_details:
#         machines = Machine.objects.filter(unit=unit_detail)
#         try:
#             for machine in machines:
#                 planning = Planning.objects.get(plan_date=current_date, machine=machine, unit=unit_detail,
#                                                 brand=brand)
#                 product_count = ProductCount.objects.filter(created_at__range=[first_range, last_range],
#                                                             plan_details=planning).count()
#                 if product_count == 0:
#                     production_count_not_updated_mail(planning)
#         except ProductCount.DoesNotExist:
#                 unit_details = "No count"
#         except Planning.DoesNotExist:
#                 unit_details = "No count"