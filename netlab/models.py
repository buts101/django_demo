from django.db import models
from django.utils import timezone
import json


class Router(models.Model):
    """Model representing a network router in the test lab"""
    ROUTER_TYPES = [
        ('PE', 'Provider Edge'),
        ('P', 'Provider'),
        ('CE', 'Customer Edge'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    router_type = models.CharField(max_length=2, choices=ROUTER_TYPES, default='PE')
    ip_address = models.GenericIPAddressField()
    loopback_ip = models.GenericIPAddressField()
    as_number = models.IntegerField(help_text="Autonomous System Number")
    mpls_enabled = models.BooleanField(default=True)
    ospf_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.router_type})"
    
    class Meta:
        ordering = ['name']


class NetworkInterface(models.Model):
    """Model representing a network interface on a router"""
    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='interfaces')
    interface_name = models.CharField(max_length=20)  # e.g., "GigabitEthernet0/0"
    ip_address = models.GenericIPAddressField()
    subnet_mask = models.CharField(max_length=15)  # e.g., "255.255.255.0"
    ospf_area = models.CharField(max_length=20, default="0.0.0.0")
    mpls_label = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.router.name} - {self.interface_name}"
    
    class Meta:
        unique_together = ['router', 'interface_name']


class NetworkTopology(models.Model):
    """Model representing the overall network topology"""
    name = models.CharField(max_length=100, default="4-Router MPLS OSPF Lab")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def get_router_count(self):
        return self.routers.count()
    
    class Meta:
        verbose_name_plural = "Network Topologies"


class TopologyRouter(models.Model):
    """Many-to-many relationship between topology and routers"""
    topology = models.ForeignKey(NetworkTopology, on_delete=models.CASCADE, related_name='routers')
    router = models.ForeignKey(Router, on_delete=models.CASCADE)
    position_x = models.IntegerField(default=0)  # For visualization
    position_y = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['topology', 'router']


class NetworkLink(models.Model):
    """Model representing connections between routers"""
    topology = models.ForeignKey(NetworkTopology, on_delete=models.CASCADE, related_name='links')
    router_a = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='links_as_a')
    interface_a = models.ForeignKey(NetworkInterface, on_delete=models.CASCADE, related_name='links_as_a')
    router_b = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='links_as_b')
    interface_b = models.ForeignKey(NetworkInterface, on_delete=models.CASCADE, related_name='links_as_b')
    bandwidth = models.IntegerField(default=1000)  # Mbps
    
    def __str__(self):
        return f"{self.router_a.name} <-> {self.router_b.name}"


class OSPFConfiguration(models.Model):
    """Model for OSPF protocol configuration"""
    router = models.OneToOneField(Router, on_delete=models.CASCADE, related_name='ospf_config')
    process_id = models.IntegerField(default=1)
    ospf_router_id = models.GenericIPAddressField()
    area = models.CharField(max_length=20, default="0.0.0.0")
    network_statements = models.TextField(help_text="JSON array of network statements")
    
    def get_networks(self):
        try:
            return json.loads(self.network_statements)
        except:
            return []
    
    def set_networks(self, networks):
        self.network_statements = json.dumps(networks)
    
    def __str__(self):
        return f"OSPF Config for {self.router.name}"


class MPLSConfiguration(models.Model):
    """Model for MPLS protocol configuration"""
    router = models.OneToOneField(Router, on_delete=models.CASCADE, related_name='mpls_config')
    ldp_router_id = models.GenericIPAddressField()
    label_range_min = models.IntegerField(default=16)
    label_range_max = models.IntegerField(default=1048575)
    
    def __str__(self):
        return f"MPLS Config for {self.router.name}"


class NetworkTest(models.Model):
    """Model representing network tests"""
    TEST_TYPES = [
        ('ping', 'Ping Test'),
        ('traceroute', 'Traceroute Test'),
        ('ospf_neighbors', 'OSPF Neighbor Test'),
        ('mpls_labels', 'MPLS Label Test'),
        ('lsp_path', 'LSP Path Test'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    topology = models.ForeignKey(NetworkTopology, on_delete=models.CASCADE, related_name='tests')
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    source_router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='tests_as_source')
    target_router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='tests_as_target', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.TextField(blank=True)
    success = models.BooleanField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.test_type} from {self.source_router.name} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
