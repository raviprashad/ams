from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import MessageForm
from .models import Message


def is_dean(user):
    return hasattr(user, 'deanprofile') 

@login_required
def create_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sent_by = request.user
            message.save()
            return redirect('/user_messages/announce/?sent=1')  # Redirect with flag
    else:
        form = MessageForm()

    # Show success box only if sent param is present in URL
    announcement_sent = request.GET.get('sent') == '1'

    return render(request, 'messages/create_message.html', {
        'form': form,
        'announcement_sent': announcement_sent
    })

    
@login_required
def message_list(request):
    user = request.user

    if hasattr(user, 'deanprofile'):
        
        messages = Message.objects.filter(sent_by=user).order_by('-created_at')

    elif hasattr(user, 'studentprofile'):
        # students see messages sent by the dean of their school --not working
        dean_users = CustomUser.objects.filter(deanprofile__school=user.school)
        messages = Message.objects.filter(
            sent_by__in=dean_users,
            for_students=True
        ).order_by('-created_at')

    else:
    
        messages = Message.objects.none()

    return render(request, 'messages/message_list.html', {'messages': messages})


@login_required
def message_detail(request, pk):
    """
    View details of a single message.
    """
    message = get_object_or_404(Message, pk=pk)
 

    return render(request, 'messages/message_detail.html', {'message': message})
