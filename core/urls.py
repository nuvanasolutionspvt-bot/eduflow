from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='login'),
    path('register/', views.SchoolRegistrationView.as_view(), name='school_register'),
    path('logout/', views.AdminLogoutView.as_view(), name='logout'),

    path('', views.WorkspaceEntryView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/add/', views.StudentCreateView.as_view(), name='student_add'),
    path('students/transliterate/', views.StudentTransliterateView.as_view(), name='student_transliterate'),
    path('students/import/', views.StudentBulkImportView.as_view(), name='student_bulk_import'),
    path('students/import/template/', views.StudentImportTemplateView.as_view(), name='student_import_template'),
    path('students/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('students/<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),

    path('settings/school/', views.SchoolSettingUpdateView.as_view(), name='school_settings'),
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    path('exams/add/', views.ExamCreateView.as_view(), name='exam_add'),
    path('exams/<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_edit'),
    path('exams/<int:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),

    path('fees/', views.FeeReceiptListView.as_view(), name='fee_receipt_list'),
    path('fees/add/', views.FeeReceiptCreateView.as_view(), name='fee_receipt_add'),
    path('fees/<int:pk>/', views.FeeReceiptDetailView.as_view(), name='fee_receipt_detail'),
    path('fees/<int:pk>/edit/', views.FeeReceiptUpdateView.as_view(), name='fee_receipt_edit'),
    path('fees/<int:pk>/delete/', views.FeeReceiptDeleteView.as_view(), name='fee_receipt_delete'),

    path('roles/', views.RoleControlView.as_view(), name='role_control'),
    path('roles/add/', views.SchoolRoleCreateView.as_view(), name='role_add'),
    path('roles/<int:pk>/edit/', views.SchoolRoleUpdateView.as_view(), name='role_edit'),
    path('roles/<int:pk>/delete/', views.SchoolRoleDeleteView.as_view(), name='role_delete'),
    path('roles/users/add/', views.SchoolUserCreateView.as_view(), name='role_user_add'),
    path('roles/users/<int:pk>/edit/', views.SchoolUserUpdateView.as_view(), name='role_user_edit'),

    path('results/', views.ResultListView.as_view(), name='result_list'),
    path('results/add/', views.ResultCreateView.as_view(), name='result_add'),
    path(
        'results/report-card/<int:student_id>/<int:exam_id>/',
        views.ResultReportCardView.as_view(),
        name='result_report_card',
    ),
    path('results/<int:pk>/edit/', views.ResultUpdateView.as_view(), name='result_edit'),
    path('results/<int:pk>/delete/', views.ResultDeleteView.as_view(), name='result_delete'),

    path('documents/id-card/', views.IDCardFormView.as_view(), name='idcard_form'),
    path('documents/id-card/bulk/', views.IDCardBulkFormView.as_view(), name='idcard_bulk_form'),
    path('documents/id-card/bulk/preview/', views.IDCardBulkPreviewView.as_view(), name='idcard_bulk_preview'),
    path('documents/id-card/bulk/html/', views.IDCardBulkHTMLView.as_view(), name='idcard_bulk_html'),
    path('documents/id-card/bulk/pdf/', views.IDCardBulkPDFView.as_view(), name='idcard_bulk_pdf'),
    path('documents/id-card/bulk/jpg/', views.IDCardBulkJPGView.as_view(), name='idcard_bulk_jpg'),
    path('documents/id-card/<int:student_id>/preview/', views.IDCardPreviewView.as_view(), name='idcard_preview'),
    path('documents/id-card/<int:student_id>/html/', views.IDCardHTMLView.as_view(), name='idcard_html'),
    path('documents/id-card/<int:student_id>/pdf/', views.IDCardPDFView.as_view(), name='idcard_pdf'),
    path('documents/id-card/<int:student_id>/jpg/', views.IDCardJPGView.as_view(), name='idcard_jpg'),

    path('documents/bonafide/', views.BonafideFormView.as_view(), name='bonafide_form'),
    path('documents/bonafide/<int:student_id>/preview/', views.BonafidePreviewView.as_view(), name='bonafide_preview'),
    path('documents/bonafide/<int:student_id>/html/', views.BonafideHTMLView.as_view(), name='bonafide_html'),
    path('documents/bonafide/<int:student_id>/pdf/', views.BonafidePDFView.as_view(), name='bonafide_pdf'),

    path('documents/nirgam/', views.NirgamFormView.as_view(), name='nirgam_form'),
    path('documents/nirgam/<int:student_id>/preview/', views.NirgamPreviewView.as_view(), name='nirgam_preview'),
    path('documents/nirgam/<int:student_id>/html/', views.NirgamHTMLView.as_view(), name='nirgam_html'),
    path('documents/nirgam/<int:student_id>/pdf/', views.NirgamPDFView.as_view(), name='nirgam_pdf'),

    path('documents/hall-ticket/', views.HallTicketFormView.as_view(), name='hallticket_form'),
    path('documents/hall-ticket/bulk/', views.HallTicketBulkFormView.as_view(), name='hallticket_bulk_form'),
    path('documents/hall-ticket/bulk/preview/', views.HallTicketBulkPreviewView.as_view(), name='hallticket_bulk_preview'),
    path('documents/hall-ticket/bulk/html/', views.HallTicketBulkHTMLView.as_view(), name='hallticket_bulk_html'),
    path('documents/hall-ticket/bulk/pdf/', views.HallTicketBulkPDFView.as_view(), name='hallticket_bulk_pdf'),
    path('documents/hall-ticket/<int:student_id>/preview/', views.HallTicketPreviewView.as_view(), name='hallticket_preview'),
    path('documents/hall-ticket/<int:student_id>/html/', views.HallTicketHTMLView.as_view(), name='hallticket_html'),
    path('documents/hall-ticket/<int:student_id>/pdf/', views.HallTicketPDFView.as_view(), name='hallticket_pdf'),
    path('templates/customize/', views.TemplateCustomizerHomeView.as_view(), name='template_customizer_home'),
    path(
        'templates/customize/<slug:document_type>/',
        views.DocumentTemplateCustomizerView.as_view(),
        name='document_template_customizer',
    ),
    path('subscription/', views.SubscriptionView.as_view(), name='subscription'),
    path('subscription/payment/create/', views.CreateSubscriptionPaymentView.as_view(), name='subscription_payment_create'),
    path('subscription/payment/verify/', views.VerifySubscriptionPaymentView.as_view(), name='subscription_payment_verify'),

    path('backup/database/', views.DatabaseBackupView.as_view(), name='database_backup'),
]
