from django.conf import settings

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

from academics.models import Subject
from users.models import TeacherProfile, StudentProfile
from .models import LeaveRequest, LeaveApproval
from .forms import LeaveRequestForm

@login_required
def apply_leave(request):
    form = LeaveRequestForm()
    success = False  

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.student = request.user
            leave.save()
            success = True  
            form = LeaveRequestForm()  

    return render(request, 'leaves/apply_leave.html', {
        'form': form,
        'success': success
    })


from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def teacher_leave_requests(request):
    if not hasattr(request.user, 'teacherprofile'):
        return render(request, 'users/error.html', {
            'message': "Teacher profile not found. Please contact admin."
        })

    approvals = LeaveApproval.objects.filter(
        teacher=request.user
    ).select_related('leave_request__student__studentprofile').order_by('-leave_request__submitted_at')

    
    status_filter = request.GET.get('filter')
    if status_filter in ['pending', 'approved', 'rejected']:
        approvals = approvals.filter(status=status_filter)

    query = request.GET.get('search')
    if query:
        approvals = approvals.filter(
            Q(leave_request__student__username__icontains=query) |
            Q(leave_request__student__first_name__icontains=query) |
            Q(leave_request__student__last_name__icontains=query)
        )

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        approvals = approvals.filter(leave_request__start_date__gte=start_date)
    if end_date:
        approvals = approvals.filter(leave_request__end_date__lte=end_date)


    paginator = Paginator(approvals, 5)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'leaves/teacher_leave_requests.html', {
        'approvals': page_obj,
        'page_obj': page_obj
    })



@login_required
def student_leave_requests(request):
    leave_requests = LeaveRequest.objects.filter(
        student=request.user
    ).prefetch_related(
        Prefetch('approvals', queryset=LeaveApproval.objects.select_related('teacher'))
    ).order_by('-submitted_at')

    return render(request, 'leaves/student_leave_requests.html', {
        'leave_requests': leave_requests
    })




@login_required
@require_POST
def leave_approval_action(request, approval_id):
    approval = get_object_or_404(
        LeaveApproval,
        id=approval_id,
        teacher=request.user
    )

    new_status = request.POST.get('status')

    if new_status not in ['approved', 'rejected']:
        return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)

    
    approval.status = new_status
    approval.save()

  
    leave = approval.leave_request
    approvals = leave.approvals.all()

    if all(a.status == 'approved' for a in approvals):
        leave.status = 'approved'
    elif any(a.status == 'rejected' for a in approvals):
        leave.status = 'rejected'
    else:
        leave.status = 'pending'

    leave.save()

    return JsonResponse({
        'status': new_status,
        'message': f'{new_status.capitalize()} successfully'
    })

