"""View module for handling requests for customer data"""
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from repairsapi.models import ServiceTicket, Employee, Customer


class TicketView(ViewSet):
    """Honey Rae API tickets view"""

    def list(self, request):
        """Handle GET requests to get all tickets

        Returns:
            Response -- JSON serialized list of tickets
        """
        service_tickets = []

        if request.auth.user.is_staff:
            service_tickets = ServiceTicket.objects.all()

        else:
            service_tickets = ServiceTicket.objects.filter(customer__user=request.auth.user)

        if "status" in request.query_params:
            if request.query_params['status'] == "done":
                service_tickets = service_tickets.filter(date_completed__isnull=False)
            
            if request.query_params['status'] == "unclaimed":
                service_tickets = service_tickets.filter(date_completed__isnull=True, employee_id__isnull=True)
            
            if request.query_params['status'] == "inprogress":
                service_tickets = service_tickets.filter(date_completed__isnull=True, employee_id__isnull=False)

            if request.query_params['status'] == "all":
                pass

        if "search" in request.query_params:
            search_terms = request.query_params['search']
            service_tickets = service_tickets.filter(description__contains=search_terms)


        serialized = ServiceTicketSerializer(service_tickets, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Handle GET requests for single ticket

        Returns:
            Response -- JSON serialized ticket record
        """

        service_ticket = ServiceTicket.objects.get(pk=pk)
        serialized = ServiceTicketSerializer(service_ticket, context={'request': request})
        return Response(serialized.data, status=status.HTTP_200_OK)
    
    def create(self, request):
        """Handle POST requests for service tickets

        Returns:
            Response: JSON serialized representation of newly created service ticket
        """
        new_ticket = ServiceTicket()
        new_ticket.customer = Customer.objects.get(user=request.auth.user)
        new_ticket.description = request.data['description']
        new_ticket.emergency = request.data['emergency']
        new_ticket.save()

        serialized = ServiceTicketSerializer(new_ticket, many=False)

        return Response(serialized.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Handle PUT requests for single ticket request
        
        Returns:
            Response -- No response body, Just 204 status code.
        """

        #Select the targeted Ticket using pk
        ticket_to_update = ServiceTicket.objects.get(pk=pk)

        # Get the employee id from the client request
        employee_id = request.data['employee']

        # Select the employee from the database using that id
        assigned_employee = Employee.objects.get(pk=employee_id)

        customer_id = request.data['customer']
        assigned_customer = Customer.objects.get(pk=customer_id)

        # Assign that Employee instance to the employee property of the ticket
        ticket_to_update.employee = assigned_employee
        ticket_to_update.customer = assigned_customer
        ticket_to_update.description = request.data['description']
        ticket_to_update.emergency = request.data['emergency']
        ticket_to_update.date_completed = request.data['date_completed']

        # Save the updated ticket
        ticket_to_update.save()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for service tickets
        
        Returns:
            Response: None with 204 status code
        """
        service_ticket = ServiceTicket.objects.get(pk=pk)
        service_ticket.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class TicketEmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = ('id', 'specialty', 'full_name')

class TicketCustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = ('id', 'address', 'full_name')

class ServiceTicketSerializer(serializers.ModelSerializer):
    """JSON serializer for tickets"""
    employee = TicketEmployeeSerializer(many=False)
    customer = TicketCustomerSerializer(many=False)

    class Meta:
        model = ServiceTicket
        fields = ('id', 'customer', 'employee', 'description', 'emergency', 'date_completed')
        depth = 1