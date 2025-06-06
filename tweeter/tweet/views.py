from django.shortcuts import render
from django.shortcuts import get_object_or_404,redirect
from .models import Tweet,Comment
from .forms import Tweetform,UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json


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
    if request.method == "POST":
        tweet = Tweet.objects.get(id=tweet_id)
        user = request.user

        liked = False
        if user in tweet.likes.all():
            tweet.likes.remove(user)
        else:
            tweet.likes.add(user)
            liked = True

        return JsonResponse({
            'liked': liked,
            'like_count': tweet.likes.count()
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
# In your views.py, modify your comment view to handle AJAX
def comment_get(request, tweet_id):
    if request.method == 'POST':
        # Your existing comment creation logic
        comment_text = request.POST.get('comment')
        tweet = get_object_or_404(Tweet, id=tweet_id)
        comment = Comment.objects.create(
            user=request.user,
            tweet=tweet,
            text=comment_text
        )
        
        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'username': comment.user.username,
                    'text': comment.text,
                    'created_at': comment.created_at.strftime("%b %d, %Y • %I:%M %p")
                }
            })
        
        # For non-AJAX requests, redirect as before
        return redirect('tweet_detail', tweet_id=tweet_id)

def comment_list(request, tweet_id):
    """
    Optional: Separate comments page (probably not needed anymore)
    """
    tweet = get_object_or_404(Tweet, id=tweet_id)
    comments = tweet.comments.all().order_by('-created_at')

    return render(request, 'comment_list.html', {
        'tweet': tweet,
        'comments': comments
    })

@login_required
def comment_delete(request, comment_id):
    """
    Delete a comment and return to the tweet page
    """
    comment = get_object_or_404(Comment, id=comment_id)
    tweet_id = comment.tweet.id
    
    # Check if user is authorized to delete the comment
    if request.user == comment.user or request.user == comment.tweet.user:
        if request.method == 'POST':
            comment.delete()
    
    return redirect('tweet_detail', tweet_id=tweet_id)

def tweet_page(request, tweet_id):
    """
    Alternative view name - calls the same function
    """
    return tweet_detail(request, tweet_id)


def tweet_detail(request, tweet_id):
    """
    Display tweet details with comments always loaded on the same page
    This should be your main tweet page view
    """
    tweet = get_object_or_404(Tweet, id=tweet_id)
    # Always load comments when displaying the tweet
    comments = tweet.comments.all().order_by('-created_at')
    
    return render(request, 'tweet_page.html', {
        'tweet': tweet,
        'comments': comments
    })

@login_required
def comment_create(request, tweet_id):
    """
    Handle comment creation and stay on the same page
    """
    tweet = get_object_or_404(Tweet, id=tweet_id)

    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        if comment_text and comment_text.strip():
            Comment.objects.create(
                tweet=tweet, 
                user=request.user, 
                text=comment_text.strip()
            )
    
    # Always redirect back to the tweet detail page
    return redirect('tweet_detail', tweet_id=tweet.id)