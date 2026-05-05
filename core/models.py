from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone
from PIL import Image, ImageOps


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class School(TimestampedModel):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='schools/logos/', blank=True, null=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SchoolSubscription(TimestampedModel):
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name='subscription',
    )
    trial_started_on = models.DateField()
    trial_expires_on = models.DateField()
    free_downloads_used = models.PositiveIntegerField(default=0)
    annual_price = models.PositiveIntegerField(default=5999)
    annual_plan_started_on = models.DateField(blank=True, null=True)
    annual_plan_expires_on = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = 'school subscription'
        verbose_name_plural = 'school subscriptions'

    def __str__(self):
        return f'{self.school.name} subscription'

    @property
    def trial_is_active(self):
        return timezone.localdate() <= self.trial_expires_on

    @property
    def annual_plan_is_active(self):
        return (
            self.annual_plan_expires_on is not None
            and timezone.localdate() <= self.annual_plan_expires_on
        )

    @property
    def remaining_free_downloads(self):
        return max(0, 1 - self.free_downloads_used)

    def activate_annual_plan(self):
        start_date = timezone.localdate()
        if self.annual_plan_expires_on and self.annual_plan_expires_on >= start_date:
            start_date = self.annual_plan_expires_on + timedelta(days=1)

        self.annual_plan_started_on = start_date
        self.annual_plan_expires_on = start_date + timedelta(days=364)


class SubscriptionPayment(TimestampedModel):
    STATUS_PENDING = 'pending'
    STATUS_VERIFIED = 'verified'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_FAILED, 'Failed'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='subscription_payments')
    subscription = models.ForeignKey(
        SchoolSubscription,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    receipt = models.CharField(max_length=40, unique=True)
    order_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, blank=True)
    signature = models.CharField(max_length=255, blank=True)
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.school.name} payment {self.receipt}'


class UserProfile(TimestampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tenant_profile')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='user_profiles', null=True, blank=True)
    is_school_admin = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'user profile'
        verbose_name_plural = 'user profiles'

    def __str__(self):
        return f'{self.user.username} profile'


class SchoolRole(TimestampedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='roles')
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='school_role')
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['school', 'name'], name='unique_role_name_per_school')
        ]

    def __str__(self):
        return f'{self.school.name} - {self.name}'


class SchoolScopedModel(TimestampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class Student(SchoolScopedModel):
    CLASS_CHOICES = [(str(i), f'Class {i}') for i in range(1, 13)]
    SECTION_CHOICES = [(s, s) for s in ['A', 'B', 'C', 'D', 'E', 'F']]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    name_mr = models.CharField(max_length=200, blank=True)
    father_name = models.CharField(max_length=200)
    father_name_mr = models.CharField(max_length=200, blank=True)
    mother_name = models.CharField(max_length=200, blank=True)
    mother_name_mr = models.CharField(max_length=200, blank=True)
    religion = models.CharField(max_length=100, blank=True)
    religion_mr = models.CharField(max_length=100, blank=True)
    caste = models.CharField(max_length=100, blank=True)
    caste_mr = models.CharField(max_length=100, blank=True)
    mother_tongue = models.CharField(max_length=100, blank=True)
    mother_tongue_mr = models.CharField(max_length=100, blank=True)
    father_occupation = models.CharField(max_length=200, blank=True)
    father_occupation_mr = models.CharField(max_length=200, blank=True)
    dob = models.DateField(verbose_name='Date of Birth')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    birth_place = models.CharField(max_length=200, blank=True)
    birth_place_mr = models.CharField(max_length=200, blank=True)
    taluka = models.CharField(max_length=200, blank=True)
    taluka_mr = models.CharField(max_length=200, blank=True)
    district = models.CharField(max_length=200, blank=True)
    district_mr = models.CharField(max_length=200, blank=True)
    student_class = models.CharField(max_length=20, choices=CLASS_CHOICES)
    section = models.CharField(max_length=5, choices=SECTION_CHOICES)
    roll_no = models.CharField(max_length=50)
    admission_no = models.CharField(max_length=50)
    register_page_no = models.CharField(max_length=100, blank=True)
    previous_school_name = models.CharField(max_length=255, blank=True)
    previous_school_name_mr = models.CharField(max_length=255, blank=True)
    previous_school_class = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    address_mr = models.TextField(blank=True)
    mobile = models.CharField(max_length=20)
    photo = models.ImageField(upload_to='students/photos/', blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=[('active', 'Active'), ('inactive', 'Inactive')],
        default='active',
    )

    class Meta:
        ordering = ['student_class', 'section', 'roll_no', 'name']
        constraints = [
            models.UniqueConstraint(fields=['school', 'admission_no'], name='unique_student_admission_per_school')
        ]

    def __str__(self):
        return f'{self.name} ({self.admission_no})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            photo_path = self.photo.path if self.photo else ''
        except (NotImplementedError, ValueError):
            return

        if self.photo and photo_path:
            with Image.open(photo_path) as img:
                # Normalize all student photos to passport ratio (3:4), fixed size 300x400.
                processed = ImageOps.fit(img.convert('RGB'), (300, 400), Image.Resampling.LANCZOS)
                ext = photo_path.lower().rsplit('.', 1)[-1]
                if ext == 'png':
                    processed.save(photo_path, format='PNG', optimize=True)
                else:
                    processed.save(photo_path, format='JPEG', quality=90)


class SchoolSetting(SchoolScopedModel):
    school_name = models.CharField(max_length=255)
    address = models.TextField()
    logo = models.ImageField(upload_to='school/logo/', blank=True, null=True)
    principal_name = models.CharField(max_length=200)
    principal_signature = models.ImageField(upload_to='school/signature/', blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['school'], name='unique_school_setting_per_school')
        ]

    def __str__(self):
        return self.school_name


class Exam(SchoolScopedModel):
    name = models.CharField(max_length=150)
    exam_date = models.DateField()

    class Meta:
        ordering = ['exam_date']

    def __str__(self):
        return f'{self.name} - {self.exam_date}'


class ExamSubject(SchoolScopedModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='subjects')
    subject_name = models.CharField(max_length=150)
    exam_date = models.DateField()

    class Meta:
        ordering = ['exam_date']

    def save(self, *args, **kwargs):
        if self.exam_id and not self.school_id:
            self.school = self.exam.school
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.subject_name} ({self.exam_date})'


class FeeReceipt(SchoolScopedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_receipts')
    receipt_no = models.CharField(max_length=30)
    receipt_date = models.DateField(default=timezone.localdate)
    tuition_fee = models.PositiveIntegerField(default=0)
    library_fee = models.PositiveIntegerField(default=0)
    lab_fee = models.PositiveIntegerField(default=0)
    sports_fee = models.PositiveIntegerField(default=0)
    other_fee = models.PositiveIntegerField(default=0)
    donation = models.PositiveIntegerField(default=0, help_text='Optional donation amount.')
    paid_amount = models.PositiveIntegerField(default=0)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-receipt_date', '-id']
        constraints = [
            models.UniqueConstraint(fields=['school', 'receipt_no'], name='unique_fee_receipt_no_per_school')
        ]

    def __str__(self):
        return f'{self.receipt_no} - {self.student.name}'

    @property
    def academic_total(self):
        return self.tuition_fee + self.library_fee + self.lab_fee + self.sports_fee + self.other_fee

    @property
    def grand_total(self):
        return self.academic_total + self.donation

    @property
    def pending_amount(self):
        return max(0, self.grand_total - self.paid_amount)

    @property
    def balance_amount(self):
        return self.pending_amount


class Result(SchoolScopedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name='results')
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['exam__name', 'student__student_class', 'student__section', 'student__roll_no', 'subject__exam_date']
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'student', 'exam', 'subject'],
                name='unique_result_per_student_exam_subject',
            )
        ]

    def __str__(self):
        return f'{self.student.name} - {self.exam.name} - {self.subject.subject_name}'

    @property
    def percentage(self):
        if not self.max_marks:
            return 0
        return round((self.marks_obtained / self.max_marks) * 100, 2)

    @property
    def status(self):
        return 'Pass' if self.percentage >= 35 else 'Fail'

    def save(self, *args, **kwargs):
        if self.student_id and not self.school_id:
            self.school = self.student.school
        super().save(*args, **kwargs)


class DocumentCounter(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='document_counters',
        null=True,
        blank=True,
    )
    doc_type = models.CharField(max_length=30)
    year = models.PositiveIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('school', 'doc_type', 'year')

    def __str__(self):
        return f'{self.doc_type} - {self.year}'


class DocumentTemplateSetting(SchoolScopedModel):
    DOCUMENT_TYPE_CHOICES = [
        ('id-card', 'ID Card'),
        ('bonafide', 'Bonafide'),
        ('nirgam', 'Nirgam'),
        ('hall-ticket', 'Hall Ticket'),
        ('report-card', 'Report Card'),
    ]
    LOGO_POSITION_CHOICES = [
        ('both', 'Both'),
        ('left', 'Left'),
        ('right', 'Right'),
        ('center', 'Center'),
        ('none', 'None'),
    ]
    TEXT_POSITION_CHOICES = [
        ('center', 'Center'),
        ('left', 'Left'),
        ('right', 'Right'),
    ]
    IMAGE_POSITION_CHOICES = [
        ('right', 'Right'),
        ('left', 'Left'),
        ('top', 'Top'),
        ('bottom', 'Bottom'),
    ]
    BORDER_STYLE_CHOICES = [
        ('accent', 'Accent Color'),
        ('double', 'Double'),
        ('solid', 'Solid'),
        ('dashed', 'Dashed'),
        ('dotted', 'Dotted'),
        ('none', 'None'),
    ]

    document_type = models.CharField(max_length=40, choices=DOCUMENT_TYPE_CHOICES)
    custom_logo = models.ImageField(upload_to='document_templates/logos/', blank=True, null=True)
    custom_signature = models.ImageField(upload_to='document_templates/signatures/', blank=True, null=True)
    accent_color = models.CharField(max_length=7, default='#cb0804')
    border_color = models.CharField(max_length=7, default='#cb0804')
    background_color = models.CharField(max_length=7, default='#f5fcc8')
    text_color = models.CharField(max_length=7, default='#000080')
    title_font_size = models.PositiveSmallIntegerField(default=38)
    text_font_size = models.PositiveSmallIntegerField(default=18)
    border_style = models.CharField(max_length=10, choices=BORDER_STYLE_CHOICES, default='accent')
    border_width = models.PositiveSmallIntegerField(default=4)
    logo_position = models.CharField(max_length=10, choices=LOGO_POSITION_CHOICES, default='both')
    text_position = models.CharField(max_length=10, choices=TEXT_POSITION_CHOICES, default='center')
    image_position = models.CharField(max_length=10, choices=IMAGE_POSITION_CHOICES, default='right')
    school_title = models.CharField(max_length=255, blank=True)
    school_address = models.TextField(blank=True)
    show_student_photo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'document_type'],
                name='unique_document_template_setting_per_school',
            )
        ]

    def __str__(self):
        return f'{self.school} - {self.document_type}'
