<?php
/**
 * Dynamic Sidebar Navigation Component with Role-Based Visibility & View Website Option
 */
require_once __DIR__ . '/check_access.php';

$current_page = basename($_SERVER['PHP_SELF']);
$user_role = $_SESSION['role'] ?? 'passenger';
?>

<!-- Modern Dark Sidebar (#1E1E2D) -->
<aside class="sidebar-wrapper bg-dark-navy text-white shadow-lg d-flex flex-column flex-shrink-0 p-3" style="width: 270px; min-height: 100vh; background-color: #1E1E2D;">
    
    <!-- Brand / Logo Header -->
    <a href="dashboard.php" class="d-flex align-items-center mb-4 text-white text-decoration-none px-2 py-1">
        <div class="brand-icon rounded-3 p-2 me-2 d-flex align-items-center justify-content-center" style="background: linear-gradient(135deg, #FF6B35, #E55A24); width: 40px; height: 40px;">
            <i class="fas fa-bus text-white fs-5"></i>
        </div>
        <span class="fs-4 fw-bold tracking-tight">Anand<span style="color: #FF6B35;">Bus</span></span>
        <span class="badge bg-primary ms-auto fs-8 px-2 py-1">Admin</span>
    </a>

    <hr class="border-secondary opacity-25 my-2">

    <!-- 🌐 QUICK ACTION: VIEW PUBLIC WEBSITE -->
    <div class="px-1 my-2">
        <a href="/" target="_blank" class="btn btn-warning w-100 fw-bold d-flex align-items-center justify-content-center gap-2 py-2 rounded-3 shadow-sm text-dark" title="Open public passenger website in new tab">
            <i class="fas fa-globe me-1 fs-6"></i>
            <span>View Website</span>
            <i class="fas fa-external-link-alt fs-8 ms-auto opacity-75"></i>
        </a>
    </div>

    <hr class="border-secondary opacity-25 my-2">

    <!-- Navigation Menu Items -->
    <ul class="nav nav-pills flex-column mb-auto gap-1">

        <!-- 1. Dashboard -->
        <?php if (has_role(['super_admin', 'manager', 'conductor'])): ?>
        <li class="nav-item">
            <a href="dashboard.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'dashboard.php') ? 'active bg-primary text-white font-semibold' : 'hover-glow'; ?>">
                <i class="fas fa-chart-line width-20"></i>
                <span>Dashboard</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 2. Buses -->
        <?php if (has_role(['super_admin', 'manager'])): ?>
        <li class="nav-item">
            <a href="buses.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'buses.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-bus-alt width-20"></i>
                <span>Buses</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 3. Routes -->
        <?php if (has_role(['super_admin', 'manager'])): ?>
        <li class="nav-item">
            <a href="routes.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'routes.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-route width-20"></i>
                <span>Routes</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 4. Bus Stops -->
        <?php if (has_role(['super_admin', 'manager', 'conductor'])): ?>
        <li class="nav-item">
            <a href="bus_stops.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'bus_stops.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-map-marker-alt width-20"></i>
                <span>Bus Stops</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 5. Schedules -->
        <?php if (has_role(['super_admin', 'manager', 'conductor'])): ?>
        <li class="nav-item">
            <a href="schedules.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'schedules.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-calendar-alt width-20"></i>
                <span>Schedules</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 6. Bookings -->
        <?php if (has_role(['super_admin', 'manager', 'conductor'])): ?>
        <li class="nav-item">
            <a href="bookings.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'bookings.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-ticket-alt width-20"></i>
                <span>Bookings</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 7. Users (Super Admin Only) -->
        <?php if (has_role(['super_admin'])): ?>
        <li class="nav-item">
            <a href="users.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'users.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-users-cog width-20"></i>
                <span>Users & Roles</span>
                <span class="badge bg-danger rounded-pill ms-auto fs-8">Admin</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 8. Student Passes -->
        <?php if (has_role(['super_admin', 'manager'])): ?>
        <li class="nav-item">
            <a href="student_passes.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'student_passes.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-id-card width-20"></i>
                <span>Student Passes</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 9. Passenger Passes -->
        <?php if (has_role(['super_admin', 'manager'])): ?>
        <li class="nav-item">
            <a href="passenger_passes.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'passenger_passes.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-address-card width-20"></i>
                <span>Passenger Passes</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 10. Special Schemes -->
        <?php if (has_role(['super_admin', 'manager'])): ?>
        <li class="nav-item">
            <a href="special_schemes.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'special_schemes.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-percentage width-20"></i>
                <span>Special Schemes</span>
            </a>
        </li>
        <?php endif; ?>

        <!-- 11. Analytics & Reports (Super Admin Only) -->
        <?php if (has_role(['super_admin'])): ?>
        <li class="nav-item">
            <a href="analytics.php" class="nav-link text-white-50 d-flex align-items-center gap-3 px-3 py-2.5 rounded-3 <?php echo ($current_page == 'analytics.php') ? 'active bg-primary text-white' : ''; ?>">
                <i class="fas fa-chart-line width-20"></i>
                <span>Analytics & Reports</span>
            </a>
        </li>
        <?php endif; ?>

    </ul>

    <hr class="border-secondary opacity-25 my-3">

    <!-- User Profile & Logout -->
    <div class="user-profile-widget p-2 rounded-3 bg-dark d-flex align-items-center justify-content-between">
        <div class="d-flex align-items-center gap-2 overflow-hidden">
            <div class="avatar rounded-circle bg-primary text-white d-flex align-items-center justify-content-center fw-bold" style="width: 36px; height: 36px; min-width: 36px;">
                <?php echo strtoupper(substr($_SESSION['user_name'] ?? 'A', 0, 1)); ?>
            </div>
            <div class="text-truncate">
                <div class="fw-semibold text-white small text-truncate"><?php echo htmlspecialchars($_SESSION['user_name'] ?? 'Admin'); ?></div>
                <small class="text-white-50 fs-8 text-uppercase"><?php echo get_role_title($user_role); ?></small>
            </div>
        </div>
        <a href="logout.php" class="text-white-50 text-hover-danger p-2" title="Logout">
            <i class="fas fa-sign-out-alt"></i>
        </a>
    </div>
</aside>

<style>
.bg-dark-navy { background-color: #1E1E2D !important; }
.nav-link.text-white-50:hover { background-color: rgba(255,255,255,0.08); color: #fff !important; }
.nav-link.active { background: linear-gradient(135deg, #1E3A5F, #2980B9) !important; color: #fff !important; font-weight: 600; }
.width-20 { width: 20px; text-align: center; }
.fs-8 { font-size: 0.72rem; }
.hover-glow:hover { transform: translateX(3px); transition: all 0.2s ease; }
</style>
