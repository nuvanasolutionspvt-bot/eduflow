from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    DocumentCounter,
    DocumentTemplateSetting,
    Exam,
    ExamSubject,
    FeeReceipt,
    Result,
    School,
    SchoolRole,
    SchoolSetting,
    SchoolSubscription,
    SubscriptionPayment,
    Student,
    UserProfile,
)


User = get_user_model()


class ExamSubjectInline(admin.TabularInline):
    model = ExamSubject
    extra = 1


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'admission_no', 'student_class', 'section', 'roll_no', 'status')
    list_filter = ('school', 'student_class', 'section', 'status')
    search_fields = ('name', 'admission_no', 'roll_no')


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(SchoolSetting)
class SchoolSettingAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'school', 'principal_name', 'updated_at')
    list_filter = ('school',)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'exam_date')
    list_filter = ('school',)
    inlines = [ExamSubjectInline]


@admin.register(FeeReceipt)
class FeeReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'school', 'student', 'receipt_date', 'grand_total', 'paid_amount', 'pending_amount')
    list_filter = ('school', 'receipt_date', 'student__student_class')
    search_fields = ('receipt_no', 'student__name', 'student__admission_no')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'school', 'exam', 'subject', 'marks_obtained', 'max_marks', 'percentage', 'status')
    list_filter = ('school', 'exam', 'student__student_class', 'subject')
    search_fields = ('student__name', 'student__admission_no', 'student__roll_no', 'subject__subject_name')


@admin.register(SchoolRole)
class SchoolRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'group', 'created_at')
    list_filter = ('school',)
    search_fields = ('name', 'school__name', 'group__name')


@admin.register(DocumentCounter)
class DocumentCounterAdmin(admin.ModelAdmin):
    list_display = ('doc_type', 'school', 'year', 'last_number')
    list_filter = ('school', 'year')


@admin.register(DocumentTemplateSetting)
class DocumentTemplateSettingAdmin(admin.ModelAdmin):
    list_display = ('document_type', 'school', 'accent_color', 'logo_position', 'text_position', 'image_position')
    list_filter = ('document_type', 'school')


@admin.register(SchoolSubscription)
class SchoolSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'school',
        'trial_started_on',
        'trial_expires_on',
        'free_downloads_used',
        'annual_price',
        'annual_plan_expires_on',
    )
    list_filter = ('trial_expires_on', 'annual_plan_expires_on')


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('school', 'receipt', 'order_id', 'payment_id', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('receipt', 'order_id', 'payment_id', 'school__name')


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    autocomplete_fields = ('school',)


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'school_name', 'is_school_admin', 'is_staff', 'is_active')
    list_filter = ('tenant_profile__school', 'tenant_profile__is_school_admin', 'is_staff', 'is_superuser', 'is_active')

    @admin.display(description='School')
    def school_name(self, obj):
        return getattr(obj.school, 'name', '')

    @admin.display(boolean=True, description='School admin')
    def is_school_admin(self, obj):
        profile = getattr(obj, 'tenant_profile', None)
        return bool(profile and profile.is_school_admin)
