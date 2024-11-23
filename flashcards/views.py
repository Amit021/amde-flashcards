from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import random
from django.db.models import Q, Count
from .models import Word, UserWordStatus, Stack


@login_required
def select_stack_view(request):
    if request.method == "POST":
        stack_id = request.POST.get("stack_id")
        request.session["selected_stack_id"] = int(stack_id)
        return redirect("flashcard")  # Redirect to the flashcard view

    stacks = Stack.objects.all()
    stack_list = []
    for stack in stacks:
        total_words = stack.words.count()
        mastered_words = UserWordStatus.objects.filter(
            user=request.user, word__stack=stack, status="mastered"
        ).count()
        percentage = (mastered_words / total_words * 100) if total_words > 0 else 0

        stack_list.append({
            'id': stack.id,
            'name': stack.name,
            'total_words': total_words,
            'mastered_words': mastered_words,
            'percentage': percentage,
        })

    context = {
        "stacks": stack_list,
    }
    return render(request, "flashcards/select_stack.html", context)


@login_required
def reset_progress(request):
    selected_stack_id = request.session.get('selected_stack_id')
    if not selected_stack_id:
        return redirect('select_stack')

    if request.method == "POST":
        UserWordStatus.objects.filter(user=request.user, word__stack_id=int(selected_stack_id)).delete()
    return redirect('flashcard')


def update_word_status(user, word_id, known):
    """
    Updates the status of a word based on the user's response.

    Parameters:
        user (User): The current logged-in user.
        word_id (int): The ID of the word being updated.
        known (bool): Whether the user marked the word as known (True) or unknown (False).
    """
    try:
        user_word_status = UserWordStatus.objects.get(user=user, word_id=word_id)
    except UserWordStatus.DoesNotExist:
        # If the status doesn't exist, create it with default 'learning' status
        user_word_status = UserWordStatus.objects.create(user=user, word_id=word_id)

    if user_word_status.status == 'learning':
        if known:
            user_word_status.times_known += 1
            if user_word_status.times_known == 2:
                # After the second known mark, transition to 'reviewing'
                user_word_status.status = 'reviewing'
                user_word_status.known_streak = 1  # Initialize streak
        else:
            # Remain in 'learning' if unknown
            user_word_status.times_known = 0  # Reset times_known if marked as unknown

    elif user_word_status.status == 'reviewing':
        if known:
            user_word_status.known_streak += 1
            if user_word_status.known_streak >= 5:
                # Transition to 'mastered' after five consecutive knowns
                user_word_status.status = 'mastered'
                user_word_status.known_streak = 0  # Reset streak
        else:
            # Reset to 'learning' and reset streak
            user_word_status.status = 'learning'
            user_word_status.known_streak = 0
            user_word_status.times_known = 0

    elif user_word_status.status == 'mastered':
        if not known:
            # If a mastered word is marked as unknown, revert to 'learning'
            user_word_status.status = 'learning'
            user_word_status.times_known = 0
            user_word_status.known_streak = 0
        else:
            # Optional: Decide if further known marks on mastered words have any effect
            # For example, you might reset the streak or leave it as is
            pass  # No action needed; word remains mastered

    user_word_status.save()



def get_next_word(user, stack, last_word_id=None, max_reviewing_words=12, max_consecutive_new_words=7, mastered_probability=0.06):
    """
    Selects the next word for the user to study based on their current progress.

    Parameters:
        user (User): The current logged-in user.
        stack (Stack): The selected stack.
        last_word_id (int, optional): The ID of the last word shown to the user.
        max_reviewing_words (int): Maximum number of words in 'reviewing' status.
        max_consecutive_new_words (int): Maximum number of new words to introduce consecutively.
        mastered_probability (float): Probability (0 to 1) to include a mastered word.

    Returns:
        Word or None: The next word to study or None if all words are mastered.
    """
    total_user_words = UserWordStatus.objects.filter(user=user, word__stack=stack)
    reviewing_words_count = total_user_words.filter(status='reviewing').count()
    learning_words = list(total_user_words.filter(status='learning'))
    reviewing_words = list(total_user_words.filter(status='reviewing'))
    mastered_words = list(total_user_words.filter(status='mastered'))

    # Check if there are any new words left in the stack
    unattempted_words = Word.objects.filter(stack=stack).exclude(
        id__in=total_user_words.values_list('word_id', flat=True)
    )

    # Introduce new words if conditions are met
    if reviewing_words_count < max_reviewing_words and len(learning_words) < max_consecutive_new_words:
        if unattempted_words.exists():
            new_word = unattempted_words.first()
            UserWordStatus.objects.create(user=user, word=new_word, status='learning')
            return new_word

    # Determine whether to select a mastered word based on probability
    if mastered_words and random.random() < mastered_probability:
        # Exclude the last shown word to avoid immediate repetition
        available_mastered = [uws for uws in mastered_words if uws.word.id != last_word_id]
        if available_mastered:
            next_mastered = random.choice(available_mastered)
            return next_mastered.word

    # Combine reviewing and learning words
    word_pool = reviewing_words + learning_words

    # Exclude the last shown word to avoid immediate repetition
    word_pool = [uws for uws in word_pool if uws.word.id != last_word_id]

    if not word_pool:
        # If no words are available in learning/reviewing, check mastered words
        if mastered_words:
            available_mastered = [uws for uws in mastered_words if uws.word.id != last_word_id]
            if available_mastered:
                next_mastered = random.choice(available_mastered)
                return next_mastered.word
        return None  # All words are mastered

    # Shuffle the pool to randomize selection
    random.shuffle(word_pool)

    # Select the first word from the shuffled pool
    next_word_status = word_pool[0]
    return next_word_status.word



def get_progress(user, stack):
    total_words = stack.words.count()
    learning = UserWordStatus.objects.filter(user=user, word__stack=stack, status='learning').count()
    reviewing = UserWordStatus.objects.filter(user=user, word__stack=stack, status='reviewing').count()
    mastered = UserWordStatus.objects.filter(user=user, word__stack=stack, status='mastered').count()

    progress = {
        'learning': (learning / total_words) * 100 if total_words else 0,
        'reviewing': (reviewing / total_words) * 100 if total_words else 0,
        'mastered': (mastered / total_words) * 100 if total_words else 0,
        'counts': {
            'learning': learning,
            'reviewing': reviewing,
            'mastered': mastered,
            'total': total_words,
        }
    }
    return progress


# flashcards/views.py

@login_required
def flashcard_view(request):
    selected_stack_id = request.session.get('selected_stack_id')
    if not selected_stack_id:
        return redirect('select_stack')

    try:
        selected_stack = Stack.objects.get(id=int(selected_stack_id))
    except (Stack.DoesNotExist, ValueError):
        del request.session['selected_stack_id']
        return redirect('select_stack')

    last_word_id = request.session.get('last_word_id')

    if request.method == 'POST':
        word_id = request.POST.get('word_id')
        skip = request.POST.get('skip') == 'true'
        if skip:
            # Update word status to 'mastered'
            user_word_status, created = UserWordStatus.objects.get_or_create(user=request.user, word_id=word_id)
            user_word_status.status = 'mastered'
            user_word_status.times_known = 0
            user_word_status.known_streak = 0
            user_word_status.save()
        else:
            known = request.POST.get('known') == 'true'
            update_word_status(request.user, word_id, known)
        request.session['last_word_id'] = int(word_id)
        return redirect('flashcard')

    next_word = get_next_word(request.user, selected_stack, last_word_id=last_word_id)

    if next_word:
        # Retrieve the UserWordStatus for the current word and user
        try:
            word_status = UserWordStatus.objects.get(user=request.user, word=next_word)
            current_status = word_status.status.capitalize()  # e.g., 'Learning', 'Reviewing', 'Mastered'
        except UserWordStatus.DoesNotExist:
            # If no status exists, assume 'Learning'
            current_status = 'Learning'

        # Process the 'german' field
        if ',' in next_word.german:
            # Assume it's a verb with multiple forms
            parts = [part.strip() for part in next_word.german.split(',')]
            infinitive = parts[0]  # First part is the infinitive
            conjugations = ', '.join(parts[1:])  # Remaining parts are conjugations
            is_verb = True
        else:
            infinitive = next_word.german
            conjugations = ''
            is_verb = False

        context = {
            'word': next_word,
            'infinitive': infinitive,
            'conjugations': conjugations,
            'is_verb': is_verb,
            'progress': get_progress(request.user, selected_stack),
            'stack': selected_stack,
            'word_status': current_status,  # Pass the status to the template
        }
        return render(request, 'flashcards/flashcard.html', context)
    else:
        return render(request, 'flashcards/completed.html', {'stack': selected_stack})



def profile_view(request):
    return render(request, "profile.html")  # Use a profile template
