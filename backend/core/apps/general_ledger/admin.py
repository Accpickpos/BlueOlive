from django.contrib import admin
from .models import GLMast, GLTran, GLStJnl, GLSpread


@admin.register(GLMast)
class GLMastAdmin(admin.ModelAdmin):
    list_display = (
        'accno', 'name', 'type', 'drorcr', 'repline', 
        'balbfwd', 'created_at', 'updated_at'
    )
    list_filter = ('type', 'drorcr', 'created_at')
    search_fields = ('accno', 'name')
    ordering = ('accno',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Account Details', {
            'fields': ('accno', 'name', 'type', 'drorcr', 'repline')
        }),
        ('Balance Information', {
            'fields': ('balbfwd',)
        }),
        ('Period Balances', {
            'fields': (
                'period1', 'period2', 'period3', 'period4', 'period5',
                'period6', 'period7', 'period8', 'period9', 'period10',
                'period11', 'period12', 'period13',
            ),
            'classes': ('collapse',)
        }),
        ('Budget Information', {
            'fields': (
                'budget1', 'budget2', 'budget3', 'budget4', 'budget5',
                'budget6', 'budget7', 'budget8', 'budget9', 'budget10',
                'budget11', 'budget12',
            ),
            'classes': ('collapse',)
        }),
        ('Last Year Balances', {
            'fields': (
                'lastyear1', 'lastyear2', 'lastyear3', 'lastyear4', 'lastyear5',
                'lastyear6', 'lastyear7', 'lastyear8', 'lastyear9', 'lastyear10',
                'lastyear11', 'lastyear12',
            ),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GLTran)
class GLTranAdmin(admin.ModelAdmin):
    list_display = (
        'batchno', 'accno', 'date', 'type', 'source', 
        'reference', 'amount', 'created_at'
    )
    list_filter = ('type', 'source', 'date', 'created_at')
    search_fields = ('batchno', 'accno', 'reference', 'details', 'station')
    ordering = ('-date', 'batchno', 'accno')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('accno', 'batchno', 'date', 'time')
        }),
        ('Classification', {
            'fields': ('type', 'source', 'station', 'reference')
        }),
        ('Amount & Description', {
            'fields': ('amount', 'details')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make critical fields readonly after creation to maintain transaction integrity."""
        if obj:  # Editing an existing object
            return self.readonly_fields + ['accno', 'batchno', 'date', 'time', 'type', 'source', 'amount']
        return self.readonly_fields


@admin.register(GLStJnl)
class GLStJnlAdmin(admin.ModelAdmin):
    list_display = (
        'journalno', 'accno', 'details', 'drorcr', 'amount',
        'frequency', 'stperiod', 'nextperiod', 'times', 'timesbal',
        'created_at', 'updated_at'
    )
    list_filter = ('drorcr', 'stperiod', 'nextperiod', 'frequency', 'created_at')
    search_fields = ('journalno', 'accno', 'details', 'descriptor')
    ordering = ('accno', 'journalno')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Journal Details', {
            'fields': ('journalno', 'accno', 'details', 'descriptor')
        }),
        ('Transaction Information', {
            'fields': ('drorcr', 'amount')
        }),
        ('Scheduling', {
            'fields': ('frequency', 'stperiod', 'nextperiod', 'times', 'timesbal')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GLSpread)
class GLSpreadAdmin(admin.ModelAdmin):
    list_display = (
        'accno', 'name', 'ytddebit', 'ytdcredit',
        'curdebit', 'curcredit', 'created_at', 'updated_at'
    )
    list_filter = ('created_at', 'updated_at')
    search_fields = ('accno', 'name')
    ordering = ('accno',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Account Details', {
            'fields': ('accno', 'name')
        }),
        ('Year-to-Date Actuals', {
            'fields': ('ytddebit', 'ytdcredit')
        }),
        ('Current Period Actuals', {
            'fields': ('curdebit', 'curcredit')
        }),
        ('Current Period Budget', {
            'fields': ('curbuddeb', 'curbudcred')
        }),
        ('Year-to-Date Budget', {
            'fields': ('ytdbuddeb', 'ytdbudcred')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )