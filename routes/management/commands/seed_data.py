"""
Management command: python manage.py seed_data
Seeds the database with:
- All 20 Anand bus stops with GPS coordinates
- 5 sample routes
- 2 buses + 2 drivers
- Sample schedules for the next 7 days
- SuperAdmin + Conductor + Passenger users
"""
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


STOPS_DATA = [
    ('ANAND_BUS_STAND',  'Anand Bus Stand (GSRTC Central)',   22.5645, 72.9289, True),
    ('VV_NAGAR',         'Vallabh Vidyanagar (V.V. Nagar)',   22.5530, 72.9215, True),
    ('BAKROL_PHATA',     'Bakrol Phata / Bakrol Square',      22.5712, 72.9103, False),
    ('MOGRI',            'Mogri',                             22.5801, 72.8942, False),
    ('KARAMSAD',         'Karamsad Cross Roads',              22.5420, 72.9452, True),
    ('VADTAL',           'Vadtal Temple Gateway',             22.4985, 72.9073, True),
    ('GAMDI',            'Gamdi',                             22.5610, 72.9350, False),
    ('LAMBHVEL',         'Lambhvel Phata',                    22.5780, 72.9520, False),
    ('CHIKHODRA',        'Chikhodra Square',                  22.5492, 72.9601, False),
    ('BORIAVI',          'Boriavi',                           22.5340, 72.9710, False),
    ('SAMARKHA',         'Samarkha',                          22.5210, 72.9830, False),
    ('JITODIA',          'Jitodia',                           22.5890, 72.9150, False),
    ('GANA',             'Gana',                              22.6010, 72.9250, False),
    ('ADAS',             'Adas',                              22.4830, 72.9100, False),
    ('ODE',              'Ode',                               22.6120, 72.9380, False),
    ('UMRETH_ROAD',      'Umreth Road',                       22.5660, 72.9420, False),
    ('TOWN_HALL',        'Town Hall Anand',                   22.5580, 72.9330, True),
    ('RAILWAY_STATION',  'Anand Railway Station Junction',    22.5720, 72.9410, True),
    ('CIVIL_HOSPITAL',   'Civil Hospital Anand',              22.5595, 72.9278, True),
    ('GIDC',             'Anand GIDC Industrial Zone',        22.5855, 72.9680, False),
]


class Command(BaseCommand):
    help = 'Seed AnandBus database with stops, routes, buses, schedules, and users'

    @transaction.atomic
    def handle(self, *args, **options):
        from routes.models import Stop, Route, RouteStop, Schedule
        from buses.models import Bus, Driver
        from accounts.models import ConductorProfile

        self.stdout.write(self.style.MIGRATE_HEADING('[+] Seeding AnandBus database...'))

        # ── Stops ────────────────────────────────────────────────────────────
        self.stdout.write('Creating stops...')
        stop_objects = {}
        for code, name, lat, lng, is_major in STOPS_DATA:
            stop, _ = Stop.objects.update_or_create(
                code=code,
                defaults={'name': name, 'latitude': lat, 'longitude': lng, 'is_major': is_major}
            )
            stop_objects[code] = stop
        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(STOPS_DATA)} stops created'))

        # ── Buses ─────────────────────────────────────────────────────────────
        self.stdout.write('Creating buses...')
        bus1, _ = Bus.objects.get_or_create(bus_number='GJ-18-T-1001', defaults={
            'bus_name': 'Anand Express',
            'bus_type': 'AC',
            'total_seats': 40,
            'has_ac': True, 'has_wifi': True, 'has_charging': True, 'has_gps': True,
        })
        bus2, _ = Bus.objects.get_or_create(bus_number='GJ-18-T-1002', defaults={
            'bus_name': 'Anand Local',
            'bus_type': 'NON_AC',
            'total_seats': 45,
            'has_gps': True,
        })
        bus3, _ = Bus.objects.get_or_create(bus_number='GJ-18-T-1003', defaults={
            'bus_name': 'VV Nagar Shuttle',
            'bus_type': 'MINI',
            'total_seats': 25,
            'has_gps': True,
        })
        self.stdout.write(self.style.SUCCESS('  [OK] 3 buses created'))

        # ── Drivers ───────────────────────────────────────────────────────────
        self.stdout.write('Creating drivers...')
        driver1, _ = Driver.objects.get_or_create(employee_id='DRV001', defaults={
            'name': 'Ramesh Patel',
            'license_number': 'GJ-18-20100010001',
            'phone': '9876543210',
            'assigned_bus': bus1,
            'experience_years': 12,
        })
        driver2, _ = Driver.objects.get_or_create(employee_id='DRV002', defaults={
            'name': 'Suresh Bhai',
            'license_number': 'GJ-18-20100010002',
            'phone': '9876543211',
            'assigned_bus': bus2,
            'experience_years': 8,
        })
        self.stdout.write(self.style.SUCCESS('  [OK] 2 drivers created'))

        # ── Routes ────────────────────────────────────────────────────────────
        self.stdout.write('Creating routes...')
        routes_data = [
            ('R01', 'Anand Central — VV Nagar Express',
             'ANAND_BUS_STAND', 'VV_NAGAR', 8.5, 12.00, 1.20,
             [('ANAND_BUS_STAND', 0, 0, 0), ('CIVIL_HOSPITAL', 1, 2.1, 10), ('TOWN_HALL', 2, 4.5, 20),
              ('RAILWAY_STATION', 3, 6.2, 30), ('VV_NAGAR', 4, 8.5, 40)]),

            ('R02', 'Anand — Karamsad — Vadtal Pilgrim Route',
             'ANAND_BUS_STAND', 'VADTAL', 22.0, 15.00, 1.50,
             [('ANAND_BUS_STAND', 0, 0, 0), ('KARAMSAD', 1, 8.0, 25), ('BORIAVI', 2, 14.5, 45),
              ('SAMARKHA', 3, 18.0, 60), ('VADTAL', 4, 22.0, 75)]),

            ('R03', 'VV Nagar — GIDC Industrial Route',
             'VV_NAGAR', 'GIDC', 12.0, 12.00, 1.30,
             [('VV_NAGAR', 0, 0, 0), ('BAKROL_PHATA', 1, 3.5, 15), ('LAMBHVEL', 2, 7.0, 30),
              ('CHIKHODRA', 3, 9.5, 42), ('GIDC', 4, 12.0, 55)]),

            ('R04', 'Anand Circular City Route',
             'ANAND_BUS_STAND', 'RAILWAY_STATION', 15.0, 10.00, 1.00,
             [('ANAND_BUS_STAND', 0, 0, 0), ('CIVIL_HOSPITAL', 1, 2.1, 10), ('GAMDI', 2, 5.0, 22),
              ('UMRETH_ROAD', 3, 9.0, 38), ('LAMBHVEL', 4, 12.0, 50), ('RAILWAY_STATION', 5, 15.0, 65)]),

            ('R05', 'Anand — Mogri — Gana Rural Route',
             'ANAND_BUS_STAND', 'GANA', 18.5, 12.00, 1.20,
             [('ANAND_BUS_STAND', 0, 0, 0), ('BAKROL_PHATA', 1, 4.5, 18), ('MOGRI', 2, 9.0, 35),
              ('JITODIA', 3, 13.5, 52), ('GANA', 4, 18.5, 70)]),
        ]

        for r_num, r_name, src, dst, dist, base, per_km, stops_seq in routes_data:
            src_stop = stop_objects[src]
            dst_stop = stop_objects[dst]
            route, created = Route.objects.get_or_create(route_number=r_num, defaults={
                'route_name': r_name,
                'source': src_stop,
                'destination': dst_stop,
                'distance_km': dist,
                'base_fare': base,
                'fare_per_km': per_km,
            })
            if created:
                # Create route stops
                cum_dist = 0.0
                for stop_code, order, dist_from_src, mins in stops_seq:
                    RouteStop.objects.create(
                        route=route,
                        stop=stop_objects[stop_code],
                        stop_order=order,
                        distance_from_source=dist_from_src,
                        scheduled_minutes_from_start=mins,
                        fare_from_source=round(base + (dist_from_src * per_km), 2),
                    )

        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(routes_data)} routes created'))

        # ── Schedules (next 7 days) ───────────────────────────────────────────
        self.stdout.write('Creating schedules...')
        today = datetime.date.today()
        schedule_templates = [
            # (route_num, bus, driver, dep_time, arr_time)
            ('R01', bus1, driver1, '06:00', '07:00'),
            ('R01', bus1, driver1, '09:00', '10:00'),
            ('R01', bus2, driver2, '12:00', '13:00'),
            ('R01', bus1, driver1, '15:00', '16:00'),
            ('R01', bus2, driver2, '18:00', '19:00'),
            ('R02', bus2, driver2, '07:00', '08:30'),
            ('R02', bus1, driver1, '14:00', '15:30'),
            ('R03', bus3, None,    '08:00', '09:00'),
            ('R03', bus3, None,    '17:00', '18:00'),
            ('R04', bus2, driver2, '06:30', '07:45'),
            ('R05', bus1, driver1, '08:00', '09:20'),
        ]

        routes_map = {r.route_number: r for r in Route.objects.all()}
        sched_count = 0
        for d_offset in range(7):
            travel_date = today + datetime.timedelta(days=d_offset)
            for r_num, bus, driver, dep, arr in schedule_templates:
                route = routes_map.get(r_num)
                if not route:
                    continue
                Schedule.objects.get_or_create(
                    route=route,
                    bus=bus,
                    travel_date=travel_date,
                    departure_time=dep,
                    defaults={
                        'driver': driver,
                        'arrival_time': arr,
                        'available_seats': bus.total_seats,
                        'status': 'SCHEDULED',
                    }
                )
                sched_count += 1
        self.stdout.write(self.style.SUCCESS(f'  [OK] {sched_count} schedules created (7 days)'))

        # ── Users ─────────────────────────────────────────────────────────────
        self.stdout.write('Creating users...')

        # SuperAdmin
        admin_user, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@anandbus.com',
            'first_name': 'Super',
            'last_name': 'Admin',
            'role': User.Role.SUPER_ADMIN,
            'is_staff': True,
            'is_superuser': True,
        })
        if created:
            admin_user.set_password('Admin@123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('  [OK] SuperAdmin: admin / Admin@123'))
        else:
            self.stdout.write('  - SuperAdmin already exists')

        # Conductor
        cond_user, created = User.objects.get_or_create(username='conductor1', defaults={
            'email': 'conductor@anandbus.com',
            'first_name': 'Ramesh',
            'last_name': 'Conductor',
            'role': User.Role.CONDUCTOR,
        })
        if created:
            cond_user.set_password('Conductor@123')
            cond_user.save()
            ConductorProfile.objects.get_or_create(
                user=cond_user,
                defaults={'employee_id': 'EMP0001', 'assigned_bus': bus1}
            )
            self.stdout.write(self.style.SUCCESS('  [OK] Conductor: conductor1 / Conductor@123'))

        # Passenger
        pax_user, created = User.objects.get_or_create(username='passenger1', defaults={
            'email': 'passenger@example.com',
            'first_name': 'Priya',
            'last_name': 'Patel',
            'role': User.Role.PASSENGER,
            'phone': '9876500001',
        })
        if created:
            pax_user.set_password('Passenger@123')
            pax_user.save()
            self.stdout.write(self.style.SUCCESS('  [OK] Passenger: passenger1 / Passenger@123'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 55))
        self.stdout.write(self.style.SUCCESS('[OK] AnandBus database seeded successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 55))
        self.stdout.write(f'  Admin Dashboard  : http://127.0.0.1:8000/buses/admin/')
        self.stdout.write(f'  Django Admin     : http://127.0.0.1:8000/django-admin/')
        self.stdout.write(f'  Home             : http://127.0.0.1:8000/')
        self.stdout.write('')
