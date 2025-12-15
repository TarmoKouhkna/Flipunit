"""
Django forms for FlipUnit.eu

FeedbackForm: Handles user feedback submission with validation
"""

from django import forms


class FeedbackForm(forms.Form):
    """
    Feedback form with character limit validation.
    
    Fields:
        feedback: TextField with max_length=1000 characters
    """
    
    feedback = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'maxlength': 1000,
            'placeholder': 'Your feedback helps us improve FlipUnit. Share your thoughts, suggestions, or report issues...',
            'class': 'hybrid-feedback-textarea',
            'aria-label': 'Feedback text',
        }),
        max_length=1000,
        required=True,
        label='Feedback',
        help_text='Maximum 1000 characters'
    )
    
    def clean_feedback(self):
        """Validate feedback text"""
        feedback = self.cleaned_data.get('feedback', '').strip()
        
        if not feedback:
            raise forms.ValidationError('Please enter your feedback.')
        
        if len(feedback) > 1000:
            raise forms.ValidationError('Feedback is too long. Maximum 1000 characters allowed.')
        
        return feedback


