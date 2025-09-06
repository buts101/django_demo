from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
import json

from .models import (
    Router, NetworkTopology, NetworkTest, OSPFConfiguration, 
    MPLSConfiguration, NetworkInterface, NetworkLink
)


def index(request):
    """Main netlab dashboard"""
    topologies = NetworkTopology.objects.filter(is_active=True)
    recent_tests = NetworkTest.objects.all()[:10]
    routers = Router.objects.all()
    
    context = {
        'topologies': topologies,
        'recent_tests': recent_tests,
        'routers': routers,
        'router_count': routers.count(),
    }
    return render(request, 'netlab/index.html', context)


def topology_detail(request, topology_id):
    """Display detailed view of a network topology"""
    topology = get_object_or_404(NetworkTopology, id=topology_id)
    routers = [tr.router for tr in topology.routers.all()]
    links = topology.links.all()
    tests = topology.tests.all()[:20]
    
    context = {
        'topology': topology,
        'routers': routers,
        'links': links,
        'tests': tests,
    }
    return render(request, 'netlab/topology_detail.html', context)


def router_detail(request, router_id):
    """Display detailed view of a router"""
    router = get_object_or_404(Router, id=router_id)
    interfaces = router.interfaces.all()
    
    try:
        ospf_config = router.ospf_config
    except OSPFConfiguration.DoesNotExist:
        ospf_config = None
    
    try:
        mpls_config = router.mpls_config
    except MPLSConfiguration.DoesNotExist:
        mpls_config = None
    
    context = {
        'router': router,
        'interfaces': interfaces,
        'ospf_config': ospf_config,
        'mpls_config': mpls_config,
    }
    return render(request, 'netlab/router_detail.html', context)


def run_test(request):
    """Run a network test"""
    if request.method == 'POST':
        test_type = request.POST.get('test_type')
        source_router_id = request.POST.get('source_router')
        target_router_id = request.POST.get('target_router')
        topology_id = request.POST.get('topology')
        
        topology = get_object_or_404(NetworkTopology, id=topology_id)
        source_router = get_object_or_404(Router, id=source_router_id)
        target_router = None
        if target_router_id:
            target_router = get_object_or_404(Router, id=target_router_id)
        
        # Create test instance
        test = NetworkTest.objects.create(
            topology=topology,
            test_type=test_type,
            source_router=source_router,
            target_router=target_router,
            status='running',
            started_at=timezone.now()
        )
        
        # Simulate running the test
        result = simulate_network_test(test)
        
        # Update test with results
        test.status = 'completed'
        test.completed_at = timezone.now()
        test.result = result['output']
        test.success = result['success']
        test.save()
        
        messages.success(request, f'Test {test.test_type} completed successfully!')
        return redirect('netlab:topology_detail', topology_id=topology.id)
    
    return redirect('netlab:index')


def simulate_network_test(test):
    """Simulate running a network test - in real implementation this would 
    interface with actual network devices"""
    
    if test.test_type == 'ping':
        if test.target_router:
            return {
                'success': True,
                'output': f"PING {test.target_router.ip_address} from {test.source_router.ip_address}\n"
                         f"64 bytes from {test.target_router.ip_address}: icmp_seq=1 ttl=64 time=1.234 ms\n"
                         f"64 bytes from {test.target_router.ip_address}: icmp_seq=2 ttl=64 time=1.123 ms\n"
                         f"--- ping statistics ---\n"
                         f"2 packets transmitted, 2 received, 0% packet loss"
            }
    
    elif test.test_type == 'ospf_neighbors':
        return {
            'success': True,
            'output': f"OSPF Neighbor Table for {test.source_router.name}:\n"
                     f"Neighbor ID     Pri   State           Dead Time   Address         Interface\n"
                     f"192.168.1.2       1   Full/DR         00:00:35    192.168.1.2     GigabitEthernet0/0\n"
                     f"192.168.1.3       1   Full/BDR        00:00:32    192.168.1.3     GigabitEthernet0/1\n"
                     f"192.168.1.4       1   Full/DROther    00:00:38    192.168.1.4     GigabitEthernet0/2"
        }
    
    elif test.test_type == 'mpls_labels':
        return {
            'success': True,
            'output': f"MPLS Label Table for {test.source_router.name}:\n"
                     f"Local  Outgoing    Prefix            Bytes Label   Outgoing   Next Hop\n"
                     f"Label  Label       or Tunnel Id      Switched      interface\n"
                     f"16     Pop Label   192.168.2.0/24    0             Gi0/0      192.168.1.2\n"
                     f"17     18          192.168.3.0/24    0             Gi0/1      192.168.1.3\n"
                     f"18     Pop Label   192.168.4.0/24    0             Gi0/2      192.168.1.4"
        }
    
    elif test.test_type == 'lsp_path':
        return {
            'success': True,
            'output': f"LSP Path from {test.source_router.name} to {test.target_router.name if test.target_router else 'all destinations'}:\n"
                     f"Path 1: {test.source_router.name} -> R2 -> R3 -> {test.target_router.name if test.target_router else 'R4'}\n"
                     f"Labels: [16, 17, 18]\n"
                     f"Total Hops: 3\n"
                     f"Path Status: Active"
        }
    
    elif test.test_type == 'traceroute':
        return {
            'success': True,
            'output': f"Traceroute from {test.source_router.name} to {test.target_router.name if test.target_router else 'unknown'}:\n"
                     f"1  192.168.1.2   1.234 ms\n"
                     f"2  192.168.2.3   2.456 ms\n"
                     f"3  {test.target_router.ip_address if test.target_router else '192.168.3.4'}   3.678 ms"
        }
    
    return {
        'success': False,
        'output': f"Unknown test type: {test.test_type}"
    }


@csrf_exempt
def test_status(request, test_id):
    """Get test status via AJAX"""
    test = get_object_or_404(NetworkTest, id=test_id)
    return JsonResponse({
        'status': test.status,
        'success': test.success,
        'result': test.result,
        'completed_at': test.completed_at.isoformat() if test.completed_at else None
    })


def topology_json(request, topology_id):
    """Return topology data as JSON for visualization"""
    topology = get_object_or_404(NetworkTopology, id=topology_id)
    
    # Prepare nodes (routers)
    nodes = []
    for tr in topology.routers.all():
        nodes.append({
            'id': tr.router.id,
            'name': tr.router.name,
            'type': tr.router.router_type,
            'ip': tr.router.ip_address,
            'x': tr.position_x,
            'y': tr.position_y,
            'mpls_enabled': tr.router.mpls_enabled,
            'ospf_enabled': tr.router.ospf_enabled,
        })
    
    # Prepare edges (links)
    edges = []
    for link in topology.links.all():
        edges.append({
            'source': link.router_a.id,
            'target': link.router_b.id,
            'bandwidth': link.bandwidth,
        })
    
    return JsonResponse({
        'nodes': nodes,
        'edges': edges,
        'name': topology.name
    })
