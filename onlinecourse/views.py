from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .models import Course, Lesson, Question, Choice, Submission, Enrollment
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        return Course.objects.all()

class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'

def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('onlinecourse:index')
    else:
        form = AuthenticationForm()
    return render(request, 'onlinecourse/login.html', {'form': form})

def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')

def registration_request(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('onlinecourse:index')
    else:
        form = UserCreationForm()
    return render(request, 'onlinecourse/registration.html', {'form': form})

def enroll(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=course_id)
        user = request.user
        if user.is_authenticated:
            Enrollment.objects.get_or_create(user=user, course=course, mode='audit')
        return redirect('onlinecourse:course_details', pk=course.id)

def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    if not user.is_authenticated:
        return redirect('onlinecourse:login')
    
    enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course, defaults={'mode': 'audit'})
    
    selected_choice_ids = request.POST.getlist('choice')
    submission = Submission.objects.create(enrollment=enrollment)
    
    for choice_id in selected_choice_ids:
        choice = get_object_or_404(Choice, pk=int(choice_id))
        submission.choices.add(choice)
        
    return redirect('onlinecourse:show_exam_result', course_id=course.id, submission_id=submission.id)

def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    selected_ids = [choice.id for choice in submission.choices.all()]
    
    grade = 0
    possible_score = 0
    
    for question in course.question_set.all():
        possible_score += question.grade
        if question.is_get_score(selected_ids):
            grade += question.grade
            
    score = int((grade / possible_score) * 100) if possible_score > 0 else 0
    passed = score >= 80

    context = {
        'course': course,
        'submission': submission,
        'selected_ids': selected_ids,
        'grade': grade,
        'possible': possible_score,
        'score': score,
        'passed': passed
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
