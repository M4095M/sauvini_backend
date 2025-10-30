from django.utils import timezone
from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsAdminUser
from .models import Purchase


def _serialize_purchase(p: Purchase):
    return {
        "id": str(p.id),
        "student_id": str(p.student.id),
        "chapter_id": str(p.chapter.id),
        "module_id": str(p.module.id),
        "price": float(p.price),
        "phone": p.phone,
        "receipt_url": p.receipt_url,
        "status": p.status,
        "reviewed_by": str(p.reviewed_by.id) if p.reviewed_by else None,
        "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None,
        "rejection_reason": p.rejection_reason,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        # Convenience details
        "student_name": f"{p.student.first_name} {p.student.last_name}",
        "student_email": p.student.user.email,
        "chapter_name": getattr(p.chapter, "name", ""),
        "module_name": getattr(p.module, "name", ""),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_list_purchases(request):
    """List purchases for admins with optional filters and pagination."""
    qs = Purchase.objects.select_related("student__user", "chapter", "module").all()

    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)

    student_id = request.query_params.get("student_id")
    if student_id:
        qs = qs.filter(student__id=student_id)

    module_id = request.query_params.get("module_id")
    if module_id:
        qs = qs.filter(module__id=module_id)

    chapter_id = request.query_params.get("chapter_id")
    if chapter_id:
        qs = qs.filter(chapter__id=chapter_id)

    reviewed_by = request.query_params.get("reviewed_by")
    if reviewed_by:
        qs = qs.filter(reviewed_by__id=reviewed_by)

    date_from = request.query_params.get("date_from")
    if date_from:
        qs = qs.filter(created_at__gte=date_from)

    date_to = request.query_params.get("date_to")
    if date_to:
        qs = qs.filter(created_at__lte=date_to)

    page = int(request.query_params.get("page", 1))
    per_page = int(request.query_params.get("per_page", 10))

    paginator = Paginator(qs.order_by("-created_at"), per_page)
    page_obj = paginator.get_page(page)

    data = {
        "purchases": [_serialize_purchase(p) for p in page_obj.object_list],
        "total": paginator.count,
        "page": page_obj.number,
        "per_page": per_page,
        "total_pages": paginator.num_pages,
    }

    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_get_purchase(request, purchase_id: str):
    try:
        purchase = Purchase.objects.select_related("student__user", "chapter", "module").get(id=purchase_id)
    except Purchase.DoesNotExist:
        return Response({"message": "Purchase not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(_serialize_purchase(purchase), status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_update_purchase_status(request, purchase_id: str):
    try:
        purchase = Purchase.objects.get(id=purchase_id)
    except Purchase.DoesNotExist:
        return Response({"message": "Purchase not found"}, status=status.HTTP_404_NOT_FOUND)

    status_value = request.data.get("status")
    rejection_reason = request.data.get("rejection_reason")

    if status_value not in {"pending", "approved", "rejected"}:
        return Response({"message": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    purchase.status = status_value
    purchase.rejection_reason = rejection_reason if status_value == "rejected" else None
    purchase.reviewed_by = getattr(request.user, "admin", None)
    purchase.reviewed_at = timezone.now()
    purchase.save(update_fields=["status", "rejection_reason", "reviewed_by", "reviewed_at", "updated_at"])

    return Response({"success": True}, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_delete_purchase(request, purchase_id: str):
    try:
        purchase = Purchase.objects.get(id=purchase_id)
    except Purchase.DoesNotExist:
        return Response({"message": "Purchase not found"}, status=status.HTTP_404_NOT_FOUND)

    purchase.delete()
    return Response({"success": True}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_purchase_statistics(request):
    qs = Purchase.objects.all()
    total = qs.count()
    pending = qs.filter(status="pending").count()
    approved = qs.filter(status="approved").count()
    rejected = qs.filter(status="rejected").count()
    total_revenue = sum(p.price for p in qs.filter(status="approved"))
    pending_revenue = sum(p.price for p in qs.filter(status="pending"))

    data = {
        "total_purchases": total,
        "pending_purchases": pending,
        "approved_purchases": approved,
        "rejected_purchases": rejected,
        "total_revenue": float(total_revenue),
        "pending_revenue": float(pending_revenue),
    }
    return Response(data, status=status.HTTP_200_OK)
