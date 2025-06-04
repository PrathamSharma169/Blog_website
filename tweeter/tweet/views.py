from django.shortcuts import render
from django.shortcuts import get_object_or_404,redirect
from .models import Tweet
from .forms import Tweetform,UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Q


# Create your views here.
def nav(request):
    return render(request,"index.html")

def tweet(request,tweet_id):
    tweet=get_object_or_404(Tweet,pk=tweet_id)
    return render(request,'tweet_page.html',{'tweet':tweet})

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

def register(request):
    if request.method=='POST':
        form=UserRegistrationForm(request.POST)
        if form.is_valid():
            user=form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login
            return redirect('tweet_list')
    else:
        form=UserRegistrationForm()
    return render(request,'registration/register.html',{'form':form})

@login_required
def my_tweets(request):
    tweets = Tweet.objects.filter(user=request.user).order_by('-created_at')  # optional sorting
    return render(request, 'mytweet.html', {'tweets': tweets})


def search_tweets(request):
    query = request.GET.get('q')
    tweets = []
    if query:
        tweets = Tweet.objects.filter(Q(title__icontains=query))
    return render(request, 'search_results.html', {'tweets': tweets, 'query': query})

@login_required
def toggle_like(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    user = request.user

    if user in tweet.likes.all():
        tweet.likes.remove(user)
    else:
        tweet.likes.add(user)

    return redirect('tweet_detail', tweet_id=tweet.id)