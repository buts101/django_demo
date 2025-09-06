from django.contrib import admin
from .models import (
    Router, NetworkInterface, NetworkTopology, TopologyRouter, 
    NetworkLink, OSPFConfiguration, MPLSConfiguration, NetworkTest
)


@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
    list_display = ['name', 'router_type', 'ip_address', 'loopback_ip', 'mpls_enabled', 'ospf_enabled']
    list_filter = ['router_type', 'mpls_enabled', 'ospf_enabled']
    search_fields = ['name', 'ip_address']


class NetworkInterfaceInline(admin.TabularInline):
    model = NetworkInterface
    extra = 1


@admin.register(NetworkInterface)
class NetworkInterfaceAdmin(admin.ModelAdmin):
    list_display = ['router', 'interface_name', 'ip_address', 'ospf_area']
    list_filter = ['ospf_area']
    search_fields = ['router__name', 'interface_name', 'ip_address']


class TopologyRouterInline(admin.TabularInline):
    model = TopologyRouter
    extra = 1


@admin.register(NetworkTopology)
class NetworkTopologyAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_router_count', 'is_active', 'created_at']
    list_filter = ['is_active']
    inlines = [TopologyRouterInline]


@admin.register(NetworkLink)
class NetworkLinkAdmin(admin.ModelAdmin):
    list_display = ['router_a', 'router_b', 'bandwidth', 'topology']
    list_filter = ['bandwidth', 'topology']


@admin.register(OSPFConfiguration)
class OSPFConfigurationAdmin(admin.ModelAdmin):
    list_display = ['router', 'process_id', 'ospf_router_id', 'area']
    search_fields = ['router__name', 'ospf_router_id']


@admin.register(MPLSConfiguration)
class MPLSConfigurationAdmin(admin.ModelAdmin):
    list_display = ['router', 'ldp_router_id', 'label_range_min', 'label_range_max']
    search_fields = ['router__name', 'ldp_router_id']


@admin.register(NetworkTest)
class NetworkTestAdmin(admin.ModelAdmin):
    list_display = ['test_type', 'source_router', 'target_router', 'status', 'success', 'created_at']
    list_filter = ['test_type', 'status', 'success', 'topology']
    search_fields = ['source_router__name', 'target_router__name']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
