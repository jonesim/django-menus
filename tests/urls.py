from django.contrib import admin
from django.urls import include, path

from tests import views

phone_patterns = ([
    path('list/', views.PhoneList.as_view(), name='phone_numbers'),
], 'phone_numbers')

nested_patterns = ([
    path('detail/', views.NestedDetail.as_view(), name='nested_detail'),
], 'nested')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('home/', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('config/', views.ConfigView.as_view(), name='config'),
    path('staff/', views.StaffOnlyView.as_view(), name='staff_only'),
    path('menu/', views.MenuView.as_view(), name='menu_view'),
    path('menu/<int:pk>/', views.MenuView.as_view(), name='menu_view_pk'),

    # requires a url argument - a bare reverse() raises NoReverseMatch
    path('month/<int:month>/', views.MonthReport.as_view(), name='month_report'),

    # the same view class under two url names
    path('multi/', views.MultiName.as_view(), name='multi_a'),
    path('multi/', views.MultiName.as_view(), name='multi_b'),

    # registry fixtures - deliberately not in alphabetical order
    path('zebra/', views.ZebraSettings.as_view(), name='zebra'),
    path('apple/', views.AppleSettings.as_view(), name='apple'),
    path('mango/', views.MangoSettings.as_view(), name='mango'),
    path('staff-settings/', views.StaffSettings.as_view(), name='staff_settings'),
    path('support-only/', views.SupportOnly.as_view(), name='support_only'),
    path('multi-section/', views.MultiSection.as_view(), name='multi_section'),
    path('reports/sales-totals/', views.SalesTotals.as_view(), name='sales_totals'),
    path('reports/breakdown/<int:year>/', views.SalesBreakdown.as_view(), name='sales_breakdown'),
    path('reports/purchase-totals/', views.PurchaseTotals.as_view(), name='purchase_totals'),
    path('reports/stock-valuation/', views.StockValuation.as_view(), name='stock_valuation'),
    path('reports/stock-staff/', views.StockStaffOnly.as_view(), name='stock_staff'),
    path('reports/company/', views.CompanyStaffOnly.as_view(), name='company_performance'),

    # namespaced include
    path('phones/', include(phone_patterns)),

    # include() that itself captures an argument
    path('section/<int:pk>/', include(nested_patterns)),
]
