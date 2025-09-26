from django.shortcuts import render
from django.shortcuts import get_object_or_404,redirect
from .models import Tweet,Comment,Collaborations
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
from django.views.decorators.csrf import csrf_exempt
import os
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from dotenv import load_dotenv
load_dotenv()

@login_required
def tweet(request,tweet_id):
    tweet= get_object_or_404(Tweet,id=tweet_id)
    collabortion= Collaborations.objects.filter(tweet=tweet)
    return render(request,'mytweet.html',{'tweets':tweet, 'collaborations':collabortion})

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

            collaborator_emails = form.cleaned_data['collaborators']
            for email in collaborator_emails:
                try:
                    user = User.objects.get(email=email)
                    Collaborations.objects.create(tweet=tweet, collaborator=user)
                except User.DoesNotExist:
                    pass  # Optionally handle users that don't exist

            return redirect('tweet_list')

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
            # Process collaborators
            collaborator_emails = form.cleaned_data.get('collaborators', [])
            for email in collaborator_emails:
                try:
                    user = User.objects.get(email=email)
                    # Skip if already a collaborator
                    if not Collaborations.objects.filter(tweet=tweet, collaborator=user).exists():
                        Collaborations.objects.create(tweet=tweet, collaborator=user)
                except User.DoesNotExist:
                    pass  # Ignore if user with that email doesn't exist

            return redirect('tweet_list')
    else:
        # Pre-fill collaborators in form for editing
        existing_collaborators = tweet.collaborators.values_list('collaborator__email', flat=True)
        form = Tweetform(
            instance=tweet,
            initial={'collaborators': ', '.join(existing_collaborators)}
        )

    return render(request, 'tweet_form.html', {'form': form})

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
    collaborations = Collaborations.objects.filter(collaborator=request.user).select_related('tweet')
    return render(request, 'mytweet.html', {'mytweets': tweets, 'collaborations': collaborations})


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
    collabortion= Collaborations.objects.filter(tweet=tweet)
    
    return render(request, 'tweet_page.html', {
        'tweet': tweet,
        'comments': comments,
        'collaborations': collabortion,
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

@login_required
@csrf_exempt
@never_cache
def ai_tweet_helper(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        text = data.get('text', '').strip()
        
        # Gemini API configuration
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # Add this to your settings.py
        GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Case 1: If text exists, rephrase and correct grammar
        if text:
            prompt = f"""Please rephrase and improve the following text by making it grammatically correct, more engaging, and suitable for a social media blog post. Keep the core message intact but make it more polished and professional:

                    Text to improve: "{text}"

                    Please return only the improved text without any additional explanations or formatting."""
            
        # Case 2: If no text but title exists, generate content
        elif title:
            prompt = f"""Write an informative, engaging, and well-structured blog post of approximately 250 words on the following topic:

                    Title: "{title}"

                    The blog should have a clear introduction, body, and conclusion. Avoid any social media formatting like hashtags, numbered threads, or emojis. Maintain a professional and inspiring tone. Return only the blog post content without any headings or extra explanations."""

            
        # Case 3: Neither title nor text provided
        else:
            return JsonResponse({
                'error': 'Please either enter a title for content generation or add text for improvement'
            }, status=400)
        
        # Prepare the request payload for Gemini API
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 1,
                "topP": 1,
                "maxOutputTokens": 2048,
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        # Make API request to Gemini
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                generated_text = result['candidates'][0]['content']['parts'][0]['text']
                return JsonResponse({
                    'success': True,
                    'generated_text': generated_text.strip(),
                    'action': 'rephrase' if text else 'generate'
                })
            else:
                return JsonResponse({'error': 'No content generated by AI'}, status=500)
        else:
            return JsonResponse({
                'error': f'AI service error: {response.status_code}'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Network error: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
    

def user_profile(request, user_id):
    """
    Display user profile with their tweets
    """
    user = get_object_or_404(User, id=user_id)
    tweets = Tweet.objects.filter(user=user).order_by('-created_at')
    # Optionally, you can also show the user's collaborations
    collaborations = Collaborations.objects.filter(collaborator=user).select_related('tweet')
    
    return render(request, 'user_profile.html', {
        'profile_user': user,
        'mytweets': tweets,
        'collaborations': collaborations
    })