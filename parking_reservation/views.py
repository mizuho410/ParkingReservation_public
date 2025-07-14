from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.db.models import Q
from datetime import date
from datetime import timedelta
from datetime import datetime as dt
import datetime 
import calendar

# 自作モジュール
from .forms import SignupForm, SearchForHomeForm, ParkingReservationForm
from .models import ParkingReservation, Employee, ParkingFeeModel, Department, MyUser


# ユーザー登録画面
class SignupView(SuccessMessageMixin, FormView):
    template_name = 'signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('login')
    success_message = "Welcome! Your account has been created successfully."

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


# ログイン画面
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 入力したメールアドレス・パスワードを格納
        email = request.POST['email']
        password = request.POST['password']
        # 入力値を元にユーザ認証
        user = authenticate(request, email=email, password=password)
        # 認証に成功した場合
        if user is not None:
            login(request, user)
            # HOME画面へ遷移（現時点ではスタブ）
            return redirect('home')
        else:
            # 認証に失敗した場合、エラーメッセージを出力
            error_message = 'メールアドレスまたはパスワードが誤っています'
            return render(request, 'login.html', {'error_message': error_message})


# home画面
class HomeView(LoginRequiredMixin, ListView):
    model = ParkingReservation
    template_name = 'home.html'
    login_url = '/login/'

    def get_week_dates(self):
        # 表示する週の日付リストを返す
        display_date = self.request.GET.get('display_date')
        direction = self.request.GET.get('direction')

        # 取得日付範囲指定
        if display_date:
            base = datetime.date.fromisoformat(display_date)
            if direction == 'prev':
                start_date = base - datetime.timedelta(days=7)
            elif direction == 'next':
                start_date = base + datetime.timedelta(days=7)
            else:
                start_date = base
        else:
            start_date = datetime.date.today()
            
        return [start_date + datetime.timedelta(days=i) for i in range(7)]

    def get_queryset(self):
        queryset = super().get_queryset()
        week_dates = self.get_week_dates()
        return queryset.filter(date__in=week_dates)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        raw_date = context['object_list']
        week_dates = self.get_week_dates()

        context['reservation_list'] = self.transform_reservation_list(raw_date,week_dates)
        context['week_dates'] = week_dates
        return context

    def transform_reservation_list(self, indata, week_dates):
        # 予約リストを画面表示用に成形する
        
        # 駐車場番号一覧を取得
        parking_nos = [1,2,3,4,5,6,7,8,9,10,11]  # 駐車場番号一覧モデルを作る場合は書き換える

        # 初期化された表示用リストを作る
        result = []
        for no in parking_nos:
            row = {
                'parking_no' : no,
                'days' : []
            }
            for d in week_dates:
                row['days'].append({
                    'date' : d,
                    'AM' : '○',
                    'PM' : '○'
                })
            result.append(row)

        # 予約データをリストに格納する
        # parking_no をキーにした辞書に変換（前処理）
        row_map = {row['parking_no']: row for row in result}

        for r in indata:
            row = row_map.get(r.parking_no)
            if not row:
                continue  # parking_no が存在しなければスキップ

            for day in row['days']:
                if day['date'] == r.date:
                    if r.day_division == '終日':
                        day['AM'] = '×'
                        day['PM'] = '×'
                    else:
                        day[r.day_division] = '×'
                    break

        return result


# 駐車場予約登録画面
class ReservationCreateView(LoginRequiredMixin, FormView):
    template_name = "create.html"
    form_class = ParkingReservationForm
    context_object_name = "reservation"
    success_url = reverse_lazy('home')
    login_url = "/login/"

    def get_initial(self):
        initial = super().get_initial()

        parking_no = self.request.GET.get('parking_no')
        date = self.request.GET.get('date')
        day_division = self.request.GET.get('day_division')

        if parking_no:
            initial['parking_no'] = parking_no
        if date:
            initial['start_date'] = date
        if day_division:
            initial['day_division'] = day_division
        if date and day_division:
            initial['reservation_type'] = 'single'

        return initial

    def form_valid(self, form):
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        parking_no = form.cleaned_data['parking_no']
        day_division = form.cleaned_data['day_division']
        reservation_holder = self.request.user.get_full_name()

        validator = ParkingReservationValidator(
            form=form,
            request=self.request,
            start_date=start_date,
            end_date=end_date,
            parking_no=parking_no,
            day_division=day_division,
            reservation_type=self.request.POST.get('reservation_type'),
        )
        if not validator.validate():
            return self.form_invalid(form)
    
        # 日付範囲で1日ずつ予約登録
        date = start_date
        while date <= end_date:
            ParkingReservation.objects.create(
                parking_no=parking_no,
                reservation_holder=reservation_holder,
                date=date,
                day_division=day_division
            )
            date += timedelta(days=1)

        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservation_holder'] = self.request.user.get_full_name()
        return context


# 駐車場予約更新画面
class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    model = ParkingReservation
    template_name = "update.html"
    fields = ['parking_no', 'reservation_holder',
              'date', 'day_division']
    success_url = reverse_lazy('my_reservations')
    login_url = "/login/"

    # バリデーション実施
    def form_valid(self, form):
        # POSTから値を取得
        date_str = self.request.POST.get("date")
        date = dt.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        parking_no = self.request.POST.get("parking_no")
        day_division = self.request.POST.get("day_division")

        validator = ParkingReservationValidatorUpd(
            form=form,
            request=self.request,
            date=date,
            parking_no=parking_no,
            day_division=day_division,
        )

        if not validator.is_valid():
            return self.form_invalid(form)

        return super().form_valid(form)


# 駐車場予約削除
class ReservationDeleteView(LoginRequiredMixin, DeleteView):
    model = ParkingReservation
    template_name = 'parkingreservation_confirm_delete.html'
    login_url = "/login/"
    success_url = reverse_lazy('my_reservations')


# 登録用バリデーションクラス
class ParkingReservationValidator:
    def __init__(self, form, request, start_date, end_date, parking_no, day_division, reservation_type):
        self.form = form
        self.request = request
        self.start_date = start_date
        self.end_date = end_date
        self.parking_no = parking_no
        self.day_division = day_division
        self.reservation_type = reservation_type

    def validate(self):
        # 連日予約のときに、終了日 > 開始日 でなければエラー
        if self.reservation_type == "multi":
            if self.start_date >= self.end_date:
                self.form.add_error("end_date", "連日予約では、終了日は開始日より後の日を選んでください。")
                return False

        # 予約日の重複チェック    
        current_date = self.start_date
        error_date = None
        while current_date <= self.end_date:
            overlapping_reservations = ParkingReservation.objects.filter(
                parking_no=self.parking_no,
                date=current_date
            )
        
            for reservation in overlapping_reservations:
                if (
                    self.day_division == "終日" and reservation.day_division in ["AM", "PM", "終日"] or
                    self.day_division == "AM" and reservation.day_division in ["AM", "終日"] or
                    self.day_division == "PM" and reservation.day_division in ["PM", "終日"]
                ):
                    error_date = current_date
                    break
                if error_date:
                    break  

            current_date += timedelta(days=1)

            if error_date:
                self.form.add_error(
                None,
                f"選択した日付は既に予約がされています。"
            )
                return False

            return True

# 更新用バリデーションクラス
class ParkingReservationValidatorUpd:
    def __init__(self, form, request, date, parking_no, day_division):
        self.form = form
        self.request = request
        self.date = date
        self.parking_no = parking_no
        self.day_division = day_division

    # 予約日の重複チェック  
    def is_valid(self):
        error_date = None  
        overlapping_reservations = ParkingReservation.objects.filter(
            parking_no=self.parking_no,
            date=self.date
        ).exclude(id=self.form.instance.id)
    
        for reservation in overlapping_reservations:
            if (
                self.day_division == "終日" and reservation.day_division in ["AM", "PM", "終日"] or
                self.day_division == "AM" and reservation.day_division in ["AM", "終日"] or
                self.day_division == "PM" and reservation.day_division in ["PM", "終日"]
            ):
                error_date = self.date
                break

        if error_date:
            self.form.add_error(
                None,
                f"選択した日付は既に予約がされています。"
            )
            return False

        return True

# 個人予約管理画面
class MyReservationsView(LoginRequiredMixin, ListView):
    model = ParkingReservation
    template_name = 'my_reservations.html'
    login_url = "/login/"

# 個人予約一覧と駐車場料金取得用
@login_required
def get_my_reservations(request):
    # 画面で選択されている表示月のデータを取得する
    month_str = request.GET.get('month')  # "YYYY-MM"

    # 表示月のデータが送られなかった場合
    if not month_str:
        return JsonResponse({'error': 'month parameter is required'}, status=400)

    # ログインユーザの氏名を取得
    full_name = request.user.get_full_name()

    # 表示月の初日と最終日を取得
    year, month = map(int, month_str.split('-'))
    start_date = datetime.date(year, month, 1)  # 月の初日
    end_date = datetime.date(
        year, month, calendar.monthrange(year, month)[1])  # 月の最終日

    # ログインユーザの予約一覧（表示月）取得
    my_reservations = ParkingReservation.objects.filter(
        reservation_holder=full_name,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    # 駐車場料金の取得
    parking_fee_obj = ParkingFeeModel.objects.first()
    parking_fee = parking_fee_obj.parking_fee if parking_fee_obj else 0

    total_fee = 0
    reservation_day_count = my_reservations.count()
    total_fee = reservation_day_count * parking_fee

    return JsonResponse({'reservations': list(my_reservations.values()), 'total_fee': total_fee})  # JSON形式で返す

# 駐車場代一覧（総務用）
class AllReservationsSummaryView(LoginRequiredMixin, TemplateView):
    template_name = 'all_reservations_summary.html'
    # アクセス権限チェック
    def dispatch(self, request, *args, **kwargs):
        try:
            if request.user.employee.department.name != "総務部":
                return HttpResponseForbidden("総務部のみアクセス可能です")
        except Employee.DoesNotExist:
            return HttpResponseForbidden("従業員情報がありません")
        except AttributeError:
            return HttpResponseForbidden("ユーザー情報が不正です")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_fee = 0

        request = self.request
        selected_department_id = request.GET.get('department')
        keyword = request.GET.get('keyword')
        selected_user_id = request.GET.get('selected_user_id')
        selected_month = request.GET.get('month')

        # 'None' を None に変換
        if selected_department_id == 'None':
            selected_department_id = None
        if not keyword or keyword.lower() in ['none', 'undefined']:
            keyword = ''
        if selected_user_id == 'None':
            selected_user_id = None
        # デフォルトで今月の予約を表示
        if not selected_month:
            today = date.today()
            selected_month = today.strftime('%Y-%m')

        # 部署と社員一覧
        departments = Department.objects.all()
        employees = Employee.objects.all()

        # 絞り込み
        if selected_department_id:
            employees = employees.filter(department_id=selected_department_id)
        if keyword:
            employees = employees.filter(
                Q(first_name__icontains=keyword) |
                Q(last_name__icontains=keyword)
            )

        reservations = None
        selected_user = None

        if selected_user_id:
            try:
                selected_user = MyUser.objects.get(id=selected_user_id)
            except MyUser.DoesNotExist:
                selected_user = None
            if selected_user:
                full_name = selected_user.get_full_name()
                reservations = ParkingReservation.objects.filter(
                    reservation_holder=full_name
                )

                # 月指定のフィルタ
                if selected_month:
                    try:
                        year, month = map(int, selected_month.split('-'))
                        start_date = date(year, month, 1)
                        last_day = calendar.monthrange(year, month)[1]
                        end_date = date(year, month, last_day)
                        reservations = reservations.filter(date__gte=start_date, date__lte=end_date)
                    except ValueError:
                        pass

                reservations = reservations.order_by('date')
                # 駐車場料金の取得
                parking_fee_obj = ParkingFeeModel.objects.first()
                parking_fee = parking_fee_obj.parking_fee if parking_fee_obj else 0
                total_fee = reservations.count() * parking_fee

        # context に代入
        context.update({
            'departments': departments,
            'selected_department_id': selected_department_id,
            'keyword': keyword,
            'employees': employees,
            'selected_user': selected_user,
            'reservations': reservations,
            'selected_month': selected_month,
            'total_fee': total_fee,
        })

        return context
