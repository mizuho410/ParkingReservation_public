from django.urls import path
from .views import SignupView, LoginView, HomeView
from django.contrib.auth.views import LogoutView
from .views import SignupView, LoginView, HomeView, ReservationCreateView, ReservationUpdateView, ReservationDeleteView, MyReservationsView, get_my_reservations, AllReservationsSummaryView

urlpatterns = [
    path('signup/', SignupView.as_view(), name = 'signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('home/', HomeView.as_view(), name='home'), 
    path('logout/', LogoutView.as_view() ,name='logout'),
    path('create/', ReservationCreateView.as_view(), name='create'),
    path('my_reservations/update/<int:pk>/', ReservationUpdateView.as_view(), name='update'),
    path('my_reservations/delete/<int:pk>/', ReservationDeleteView.as_view(), name='delete'),
    path('my_reservations/', MyReservationsView.as_view(), name='my_reservations'),
    path('get_my_reservations/', get_my_reservations),
    path('all_reservations_summary/', AllReservationsSummaryView.as_view(), name='all_reservations_summary'),
]
