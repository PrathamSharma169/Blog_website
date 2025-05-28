from django.shortcuts import render
from django.shortcuts import get_object_or_404,redirect
from .models import Tweet
from .forms import Tweetform,UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login


# Create your views here.
def nav(request):
    return render(request,"index.html")

def tweet_list(request):
    tweets=Tweet.objects.all().order_by('created_at')
    return render(request,'tweet_list.html',{'tweets':tweets}) # is html page pr tweets object bhi jayga

@login_required
def create_tweet(request):
    if request.method == "POST":
        form=Tweetform(request.POST, request.FILES)
        if form.is_valid():
            tweet=form.save(commit=False)
            tweet.user=request.user
            tweet.save()
            return redirect(tweet_list)

    else:
        form=Tweetform()
        return render(request,'tweet_form.html',{'form':form})
    
@login_required
def edit_tweet(request,tweet_id):
    tweet=get_object_or_404(Tweet,pk=tweet_id,user=request.user)
    if request.method=="POST":
        form=Tweetform(request.POST,request.FILES,instance=tweet)
        if form.is_valid():
            tweet=form.save(commit=False)
            tweet.user=request.user
            tweet.save()
            return redirect('tweet_list')
    else:
        form = Tweetform(instance=tweet)
    return render(request,'tweet_form.html',{'form':form})

@login_required
def delete_tweet(request,tweet_id):
    tweet=get_object_or_404(Tweet,pk=tweet_id,user=request.user)
    if request.method=='POST':
        tweet.delete()
        return redirect('tweet_list')
    return render(request,'tweet_confirm_delete.html',{'tweet':tweet})

def login(request):
    if request.method=='POST':
        form=UserRegistrationForm()
        if form.is_valid():
            user=form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login
            return redirect('tweet_list')
    else:
        form=UserRegistrationForm()
    return render(request,'registeration/register.html',{'form':form})