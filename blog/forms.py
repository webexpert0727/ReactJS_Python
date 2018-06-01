from django import forms
from blog.models import Category, Post


MAX_COLS_NUM = 160


class PostForm(forms.ModelForm):
    # content = forms.CharField(widget=forms.Textarea(
    #     attrs={
    #         'cols': MAX_COLS_NUM,
    #         'rows': '40'
    #     }
    # ))

    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'size': MAX_COLS_NUM // 2
                }),

            'author': forms.TextInput(
                attrs={
                    'size': MAX_COLS_NUM // 2
                }),

            'tags': forms.CheckboxSelectMultiple,

            'category': forms.RadioSelect,

            'preview': forms.Textarea(
                attrs={
                    'cols': MAX_COLS_NUM / 2,
                    'rows': '8'
                }),
            'slug': forms.TextInput(
                attrs={
                    'size': MAX_COLS_NUM / 2,
                }),
        }
