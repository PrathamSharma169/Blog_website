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
from django.views.decorators.csrf import csrf_protect
import logging
from django.utils.timezone import localtime
import requests

@login_required
def tweet(request,tweet_id):
    tweet= get_object_or_404(Tweet,id=tweet_id)
    return render(request,'mytweet.html',{'tweets':tweet})

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
@require_POST
def comment_get(request, tweet_id):
    """
    Handle comment creation with AJAX support
    """
    tweet = get_object_or_404(Tweet, id=tweet_id)
    comment_text = request.POST.get('comment', '').strip()
    url = "https://twiter-sentiment-analysis.onrender.com/api/predict"

    # The tweet to analyze
    data = {
        "tweet": comment_text
    }

    # Send POST request
    response = requests.post(url, json=data)
    result=response.json()
    if not comment_text:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Comment cannot be empty'})
        return redirect('tweet_detail', tweet_id=tweet_id)
    
    # Create the comment
    comment = Comment.objects.create(
        user=request.user,
        tweet=tweet,
        text=comment_text,
        sentiment= result["sentiment"]
    )
    
    # If it's an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'username': comment.user.username,
                'text': comment.text,
                'created_at': localtime(comment.created_at).strftime("%b %d, %Y • %I:%M %p"),
                'can_delete': True  # Since the current user created it
            },
            'comment_count': tweet.comments.count()
        })
    
    # For non-AJAX requests (fallback), redirect as before
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

logger = logging.getLogger(__name__)

@login_required
@require_POST
@csrf_protect
def comment_delete(request, comment_id,tweet_id):
    """
    Delete a comment with AJAX support
    """
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        tweet = comment.tweet
        
        # Check if user is authorized to delete the comment
        if request.user == comment.user or request.user == tweet.user:
            # Get comment count before deletion
            comment_count_before = tweet.comments.count()
            comment_id = comment.id
            # Delete the comment
            comment.delete()
            
            # Get updated comment count
            comment_count_after = tweet.comments.count()
            
            logger.info(f"Comment {comment_id} deleted by user {request.user.id}")
            
            # If it's an AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment_id': comment_id,
                    'comment_count': comment_count_after,
                    'message': 'Comment deleted successfully'
                })
            
            # For non-AJAX requests, redirect
            return redirect('tweet_detail', tweet_id=tweet.id)
            
        else:
            logger.warning(f"Unauthorized delete attempt for comment {comment_id} by user {request.user.id}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'error': 'You are not authorized to delete this comment'
                }, status=403)
            
            # For non-AJAX requests, redirect with error
            return redirect('tweet_detail', tweet_id=comment.tweet.id)
            
    except Comment.DoesNotExist:
        logger.error(f"Comment {comment_id} not found")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Comment not found'
            }, status=404)
        
        return redirect('home')  # or appropriate fallback
        
    except Exception as e:
        logger.error(f"Error deleting comment {comment_id}: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while deleting the comment'
            }, status=500)
        
        return redirect('tweet_detail', tweet_id=comment.tweet.id)

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
    Redirect to the main comment handler
    """
    return comment_get(request, tweet_id)

@login_required
def sentiment_list(request,tweet_id,sentiment):
    """
    List comments by sentiment
    """
    tweet = get_object_or_404(Tweet, id=tweet_id)
    comments = tweet.comments.filter(sentiment=sentiment).order_by('-created_at')
    positive_count = tweet.comments.filter(sentiment='positive').count()
    negative_count = tweet.comments.filter(sentiment='negative').count()
    neutral_count = tweet.comments.filter(sentiment='neutral').count()
    return render(request, 'sentiment_list.html', {
        'tweet': tweet,
        'comments': comments,
        'sentiment': sentiment,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count
    })

@login_required
def comment_sentiment_list(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    comment_negative = tweet.comments.filter(sentiment='negative').count()
    comment_positive = tweet.comments.filter(sentiment='positive').count()
    comment_neutral = tweet.comments.filter(sentiment='neutral').count()
    return render(request, 'comment_analysis.html', {
        'tweet': tweet,
        'comment_negative': comment_negative,
        'comment_positive': comment_positive, 
        'comment_neutral': comment_neutral
    })