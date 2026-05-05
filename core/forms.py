from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.forms import inlineformset_factory
from .models import Exam, ExamSubject, FeeReceipt, Result, School, SchoolRole, SchoolSetting, Student
from .translation import translate_text


User = get_user_model()


class DateInput(forms.DateInput):
    input_type = 'date'


class StudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Student
        fields = [
            'name',
            'name_mr',
            'father_name',
            'father_name_mr',
            'mother_name',
            'mother_name_mr',
            'religion',
            'religion_mr',
            'caste',
            'caste_mr',
            'mother_tongue',
            'mother_tongue_mr',
            'father_occupation',
            'father_occupation_mr',
            'dob',
            'gender',
            'birth_place',
            'birth_place_mr',
            'taluka',
            'taluka_mr',
            'district',
            'district_mr',
            'student_class',
            'section',
            'roll_no',
            'admission_no',
            'register_page_no',
            'previous_school_name',
            'previous_school_name_mr',
            'previous_school_class',
            'address',
            'address_mr',
            'mobile',
            'photo',
            'status',
        ]
        labels = {
            'name': 'Student Name',
            'name_mr': 'Student Name (Marathi)',
            'father_name': 'Father Name',
            'father_name_mr': 'Father Name (Marathi)',
            'mother_name': 'Mother Name',
            'mother_name_mr': 'Mother Name (Marathi)',
            'religion': 'Religion',
            'religion_mr': 'Religion (Marathi)',
            'caste': 'Caste',
            'caste_mr': 'Caste (Marathi)',
            'mother_tongue': 'Mother Tongue',
            'mother_tongue_mr': 'Mother Tongue (Marathi)',
            'father_occupation': 'Occupation of Father',
            'father_occupation_mr': 'Occupation of Father (Marathi)',
            'dob': 'Date of Birth',
            'gender': 'Gender',
            'birth_place': 'Birth Place',
            'birth_place_mr': 'Birth Place (Marathi)',
            'taluka': 'Taluka',
            'taluka_mr': 'Taluka (Marathi)',
            'district': 'District',
            'district_mr': 'District (Marathi)',
            'student_class': 'Class',
            'section': 'Section',
            'roll_no': 'Roll No',
            'admission_no': 'Admission No',
            'register_page_no': 'Nirgam Register Page No',
            'previous_school_name': 'Previous School Name',
            'previous_school_name_mr': 'Previous School Name (Marathi)',
            'previous_school_class': 'Previous School Class',
            'address': 'Address',
            'address_mr': 'Address (Marathi)',
            'mobile': 'Mobile',
            'photo': 'Photo',
            'status': 'Status',
        }
        widgets = {
            'dob': DateInput(),
            'address': forms.Textarea(attrs={'rows': 2}),
            'address_mr': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        auto_pairs = [
            ('name', 'name_mr'),
            ('father_name', 'father_name_mr'),
            ('mother_name', 'mother_name_mr'),
            ('religion', 'religion_mr'),
            ('caste', 'caste_mr'),
            ('mother_tongue', 'mother_tongue_mr'),
            ('father_occupation', 'father_occupation_mr'),
            ('birth_place', 'birth_place_mr'),
            ('taluka', 'taluka_mr'),
            ('district', 'district_mr'),
            ('previous_school_name', 'previous_school_name_mr'),
            ('address', 'address_mr'),
        ]
        for source_field, target_field in auto_pairs:
            source_value = (cleaned_data.get(source_field) or '').strip()
            target_value = (cleaned_data.get(target_field) or '').strip()
            if source_value and (not target_value or target_value == source_value):
                cleaned_data[target_field] = translate_text(source_value)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.school is not None:
            instance.school = self.school
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class StudentBulkImportForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel file',
        help_text='Upload .xlsx file using the provided format template.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['excel_file'].widget.attrs['class'] = 'form-control'

    def clean_excel_file(self):
        excel_file = self.cleaned_data['excel_file']
        file_name = (excel_file.name or '').lower()
        if not file_name.endswith('.xlsx'):
            raise forms.ValidationError('Please upload a .xlsx file.')
        return excel_file


class SchoolSettingForm(forms.ModelForm):
    class Meta:
        model = SchoolSetting
        fields = ['school_name', 'address', 'logo', 'principal_name', 'principal_signature']
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SchoolRegistrationForm(UserCreationForm):
    school_name = forms.CharField(max_length=255, label='School name')
    school_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='School address')
    school_logo = forms.ImageField(required=False, label='School logo')
    admin_email = forms.EmailField(label='Admin email')
    principal_name = forms.CharField(max_length=200, label='Principal name')

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'admin_email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Admin username'
        self.fields['admin_email'].widget.attrs['placeholder'] = 'admin@school.com'
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-control'
            else:
                existing_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f'{existing_class} form-control'.strip()

    def clean_school_name(self):
        school_name = (self.cleaned_data.get('school_name') or '').strip()
        if School.objects.filter(name__iexact=school_name).exists():
            raise forms.ValidationError('A school with this name is already registered.')
        return school_name


ROLE_FEATURES = [
    (
        'students',
        'Student Management',
        ['core.view_student', 'core.add_student', 'core.change_student', 'core.delete_student'],
    ),
    (
        'fees',
        'Fee Management',
        ['core.view_feereceipt', 'core.add_feereceipt', 'core.change_feereceipt', 'core.delete_feereceipt'],
    ),
    (
        'documents',
        'Documents Generation',
        ['core.view_student', 'core.view_exam', 'core.view_documenttemplatesetting'],
    ),
    (
        'exams',
        'Manage Exams',
        ['core.view_exam', 'core.add_exam', 'core.change_exam', 'core.delete_exam'],
    ),
    (
        'results',
        'Results',
        ['core.view_result', 'core.add_result', 'core.change_result', 'core.delete_result'],
    ),
    (
        'school_settings',
        'School Settings',
        ['core.view_schoolsetting', 'core.change_schoolsetting'],
    ),
    (
        'templates',
        'Customize Templates',
        ['core.view_documenttemplatesetting', 'core.add_documenttemplatesetting', 'core.change_documenttemplatesetting'],
    ),
    (
        'roles',
        'Role Control',
        [
            'core.view_schoolrole',
            'core.add_schoolrole',
            'core.change_schoolrole',
            'core.delete_schoolrole',
            'auth.view_user',
            'auth.add_user',
            'auth.change_user',
        ],
    ),
    (
        'backup',
        'Backup Database',
        ['core.view_schoolsetting'],
    ),
]


def _permissions_for_feature_keys(feature_keys):
    permission_codes = []
    for key, _label, codes in ROLE_FEATURES:
        if key in feature_keys:
            permission_codes.extend(codes)
    query = Q()
    for code in permission_codes:
        app_label, codename = code.split('.', 1)
        query |= Q(content_type__app_label=app_label, codename=codename)
    if not permission_codes:
        return Permission.objects.none()
    return Permission.objects.filter(query)


class SchoolRoleForm(forms.ModelForm):
    features = forms.MultipleChoiceField(
        choices=[(key, label) for key, label, _codes in ROLE_FEATURES],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Access Permissions',
    )

    class Meta:
        model = SchoolRole
        fields = ['name', 'features']

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            permission_codes = {
                f'{permission.content_type.app_label}.{permission.codename}'
                for permission in self.instance.group.permissions.select_related('content_type')
            }
            self.fields['features'].initial = [
                key for key, _label, codes in ROLE_FEATURES if set(codes).issubset(permission_codes)
            ]
        self.fields['name'].widget.attrs['class'] = 'form-control'

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if self.school is not None:
            queryset = SchoolRole.objects.filter(school=self.school, name__iexact=name)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('A role with this name already exists.')
        return name

    def selected_permissions(self):
        return _permissions_for_feature_keys(self.cleaned_data.get('features') or [])


class SchoolUserForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text='Required for new users. Leave blank while editing to keep the current password.',
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=SchoolRole.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    is_active = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        if self.school is not None:
            self.fields['roles'].queryset = SchoolRole.objects.filter(school=self.school).select_related('group')
        if self.instance is not None:
            self.fields['username'].initial = self.instance.username
            self.fields['email'].initial = self.instance.email
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['is_active'].initial = self.instance.is_active
            self.fields['roles'].initial = SchoolRole.objects.filter(
                school=self.school,
                group__in=self.instance.groups.all(),
            )
        for name, field in self.fields.items():
            if name not in {'roles', 'is_active'}:
                field.widget.attrs['class'] = 'form-control'
            elif name == 'is_active':
                field.widget.attrs['class'] = 'form-check-input'

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        queryset = User.objects.filter(username__iexact=username)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('A user with this username already exists.')
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password') or ''
        if self.instance is None and not password:
            raise forms.ValidationError('Password is required for new users.')
        return password


class StudentSelectForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        widget=forms.Select(attrs={'class': 'select2'}),
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        queryset = Student.objects.none()
        if school is not None:
            queryset = Student.objects.filter(school=school, status='active').order_by('name')
        self.fields['student'].queryset = queryset
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if 'select2' in css:
                field.widget.attrs['class'] = f'{css} form-select'.strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class BonafideForm(StudentSelectForm):
    pass


class IDCardBulkForm(forms.Form):
    student_class = forms.ChoiceField(choices=Student.CLASS_CHOICES, label='Class')
    section = forms.ChoiceField(
        choices=[('', 'All Sections')] + Student.SECTION_CHOICES,
        required=False,
        label='Section',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class NirgamForm(StudentSelectForm):
    LANGUAGE_CHOICES = [
        ('mr', 'Marathi'),
        ('en', 'English'),
    ]

    leaving_date = forms.DateField(widget=DateInput())
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES, initial='mr')
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))
    conduct_remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))


class HallTicketForm(StudentSelectForm):
    exam = forms.ModelChoiceField(queryset=Exam.objects.none(), empty_label='Select exam')
    seat_number = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        school = kwargs.get('school')
        super().__init__(*args, **kwargs)
        exams = Exam.objects.none()
        if school is not None:
            exams = Exam.objects.filter(school=school).order_by('-id')
        self.fields['exam'].queryset = exams
        if not exams.exists():
            self.fields['exam'].help_text = 'No exams found. Add an exam first.'


class HallTicketBulkForm(forms.Form):
    exam = forms.ModelChoiceField(queryset=Exam.objects.none(), empty_label='Select exam')
    student_class = forms.ChoiceField(choices=Student.CLASS_CHOICES, label='Class')
    section = forms.ChoiceField(
        choices=[('', 'All Sections')] + Student.SECTION_CHOICES,
        required=False,
        label='Section',
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        exams = Exam.objects.none()
        if school is not None:
            exams = Exam.objects.filter(school=school).order_by('-id')
        self.fields['exam'].queryset = exams
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        if not exams.exists():
            self.fields['exam'].help_text = 'No exams found. Add an exam first.'


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ExamTermsForm(forms.Form):
    first_term = forms.CharField(max_length=150, label='First term')
    second_term = forms.CharField(max_length=150, label='Second term')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


ExamSubjectFormSet = inlineformset_factory(
    Exam,
    ExamSubject,
    fields=('subject_name', 'exam_date'),
    extra=3,
    can_delete=True,
    widgets={
        'subject_name': forms.TextInput(attrs={'class': 'form-control'}),
        'exam_date': DateInput(attrs={'class': 'form-control'}),
    },
)


class FeeReceiptForm(forms.ModelForm):
    class Meta:
        model = FeeReceipt
        fields = [
            'student',
            'receipt_date',
            'tuition_fee',
            'library_fee',
            'lab_fee',
            'sports_fee',
            'other_fee',
            'donation',
            'paid_amount',
            'remarks',
        ]
        labels = {
            'receipt_date': 'Receipt Date',
            'tuition_fee': 'Tuition',
            'library_fee': 'Library',
            'lab_fee': 'Lab',
            'sports_fee': 'Sports',
            'other_fee': 'Other',
            'donation': 'Donation (Optional)',
            'paid_amount': 'Paid',
        }
        widgets = {
            'receipt_date': DateInput(),
            'remarks': forms.TextInput(attrs={'placeholder': 'Optional note'}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if self.school is not None:
            self.fields['student'].queryset = Student.objects.filter(
                school=self.school,
                status='active',
            ).order_by('name')
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select select2'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean_paid_amount(self):
        paid_amount = self.cleaned_data.get('paid_amount') or 0
        academic_total = sum(
            self.cleaned_data.get(field) or 0
            for field in ['tuition_fee', 'library_fee', 'lab_fee', 'sports_fee', 'other_fee']
        )
        grand_total = academic_total + (self.cleaned_data.get('donation') or 0)
        if paid_amount > grand_total:
            raise forms.ValidationError('Paid amount cannot be greater than grand total.')
        return paid_amount

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.school is not None:
            instance.school = self.school
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ResultForm(forms.ModelForm):
    subject_name = forms.CharField(
        max_length=150,
        label='Subject',
    )

    class Meta:
        model = Result
        fields = ['student', 'exam', 'marks_obtained', 'max_marks', 'remarks']
        labels = {
            'marks_obtained': 'Marks Obtained',
            'max_marks': 'Max Marks',
        }
        widgets = {
            'remarks': forms.TextInput(attrs={'placeholder': 'Optional note'}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if self.school is not None:
            self.fields['student'].queryset = Student.objects.filter(
                school=self.school,
                status='active',
            ).order_by('student_class', 'section', 'roll_no', 'name')
            self.fields['exam'].queryset = Exam.objects.filter(school=self.school).order_by('-id')
        if self.instance.pk and self.instance.subject_id:
            self.fields['subject_name'].initial = self.instance.subject.subject_name
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select select2'
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['marks_obtained'].widget.attrs['min'] = '0'
        self.fields['max_marks'].widget.attrs['min'] = '1'

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        exam = cleaned_data.get('exam')
        subject_name = (cleaned_data.get('subject_name') or '').strip()
        marks_obtained = cleaned_data.get('marks_obtained')
        max_marks = cleaned_data.get('max_marks')

        if self.school is not None:
            for obj, label in [(student, 'student'), (exam, 'exam')]:
                if obj is not None and obj.school_id != self.school.id:
                    raise forms.ValidationError(f'Selected {label} does not belong to your school.')

        if marks_obtained is not None and max_marks is not None and marks_obtained > max_marks:
            self.add_error('marks_obtained', 'Marks obtained cannot be greater than max marks.')

        subject = None
        if exam is not None and subject_name:
            subject = ExamSubject.objects.filter(
                school=self.school,
                exam=exam,
                subject_name__iexact=subject_name,
            ).first()

        if student is not None and exam is not None and subject is not None:
            duplicate = Result.objects.filter(
                school=self.school,
                student=student,
                exam=exam,
                subject=subject,
            )
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise forms.ValidationError('Result for this student, exam and subject already exists.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.school is not None:
            instance.school = self.school
        subject_name = (self.cleaned_data.get('subject_name') or '').strip()
        if subject_name and instance.exam_id:
            subject = ExamSubject.objects.filter(
                school=instance.school,
                exam=instance.exam,
                subject_name__iexact=subject_name,
            ).first()
            if subject is None:
                subject = ExamSubject.objects.create(
                    school=instance.school,
                    exam=instance.exam,
                    subject_name=subject_name,
                    exam_date=instance.exam.exam_date,
                )
            instance.subject = subject
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ResultBulkEntryForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.none())
    first_term = forms.ModelChoiceField(queryset=Exam.objects.none(), label='First Term')
    second_term = forms.ModelChoiceField(
        queryset=Exam.objects.none(),
        label='Second Term',
        required=False,
        help_text='Optional. Select this to enter both terms together.',
    )

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if self.school is not None:
            self.fields['student'].queryset = Student.objects.filter(
                school=self.school,
                status='active',
            ).order_by('student_class', 'section', 'roll_no', 'name')
            exams = Exam.objects.filter(school=self.school).order_by('-id')
            self.fields['first_term'].queryset = exams
            self.fields['second_term'].queryset = exams
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select select2'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        first_term = cleaned_data.get('first_term')
        second_term = cleaned_data.get('second_term')
        if first_term is not None and second_term is not None and first_term.id == second_term.id:
            self.add_error('second_term', 'Second term must be different from first term.')
        return cleaned_data


class AdminAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


