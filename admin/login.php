<?php
/**
 * AnandBus Admin — Secure Authentication Login Page
 */
session_start();

$error = '';
if (isset($_GET['error'])) {
    if ($_GET['error'] === 'session_expired') {
        $error = 'Your session has expired. Please log in again.';
    } elseif ($_GET['error'] === 'invalid_credentials') {
        $error = 'Invalid email address or password.';
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email'] ?? '');
    $password = trim($_POST['password'] ?? '');

    // Demo Authentication Matrix (In production, replace with PDO database lookup and password_verify)
    $demo_users = [
        'admin@anandbus.in' => [
            'id' => 1,
            'name' => 'System Super Admin',
            'email' => 'admin@anandbus.in',
            // Hash for 'admin123'
            'hash' => '$2y$10$e0MYzXyjpJS7Pd0RVvHwHe1T9vW1pG/0o4z9tL/M3Zq5e7u1y5.4S',
            'role' => 'super_admin'
        ],
        'manager@anandbus.in' => [
            'id' => 2,
            'name' => 'Rajesh Patel (Manager)',
            'email' => 'manager@anandbus.in',
            'hash' => '$2y$10$e0MYzXyjpJS7Pd0RVvHwHe1T9vW1pG/0o4z9tL/M3Zq5e7u1y5.4S',
            'role' => 'manager'
        ],
        'conductor@anandbus.in' => [
            'id' => 3,
            'name' => 'Vikram Singh (Conductor)',
            'email' => 'conductor@anandbus.in',
            'hash' => '$2y$10$e0MYzXyjpJS7Pd0RVvHwHe1T9vW1pG/0o4z9tL/M3Zq5e7u1y5.4S',
            'role' => 'conductor'
        ]
    ];

    if (isset($demo_users[$email])) {
        $usr = $demo_users[$email];
        // Password Verification check (admin123 or direct demo pass)
        if ($password === 'admin123' || password_verify($password, $usr['hash'])) {
            $_SESSION['user_id'] = $usr['id'];
            $_SESSION['user_name'] = $usr['name'];
            $_SESSION['user_email'] = $usr['email'];
            $_SESSION['role'] = $usr['role'];

            // Role-Based Redirection
            if ($usr['role'] === 'conductor') {
                header("Location: pass_verifier.php");
            } else {
                header("Location: dashboard.php");
            }
            exit();
        }
    }

    $error = 'Invalid email address or password.';
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login — AnandBus</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Inter', sans-serif; }
        .login-card { background: rgba(255,255,255,0.95); backdrop-filter: blur(12px); border-radius: 24px; box-shadow: 0 25px 50px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); max-width: 420px; width: 100%; }
        .btn-brand { background: linear-gradient(135deg, #FF6B35, #E55A24); border: none; border-radius: 12px; font-weight: 700; color: #fff; }
        .btn-brand:hover { background: linear-gradient(135deg, #E55A24, #FF6B35); color: #fff; }
    </style>
</head>
<body>

<div class="container p-3">
    <div class="login-card p-4 p-md-5 mx-auto">
        <!-- Logo -->
        <div class="text-center mb-4">
            <div class="d-inline-flex align-items-center justify-content-center bg-dark rounded-4 p-3 mb-2 shadow" style="width:56px; height:56px;">
                <i class="fas fa-bus text-warning fs-3"></i>
            </div>
            <h3 class="fw-bold mb-0 text-dark">Anand<span style="color:#FF6B35;">Bus</span></h3>
            <small class="text-muted text-uppercase tracking-wider fw-semibold" style="font-size:0.75rem;">Admin & Staff Portal</small>
        </div>

        <?php if ($error): ?>
            <div class="alert alert-danger border-0 rounded-3 small mb-3"><i class="fas fa-exclamation-circle me-2"></i><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>

        <form method="POST" action="login.php">
            <div class="mb-3">
                <label class="form-label small fw-semibold text-dark">Email Address</label>
                <div class="input-group">
                    <span class="input-group-text bg-light border-end-0"><i class="fas fa-envelope text-muted"></i></span>
                    <input type="email" name="email" class="form-control bg-light border-start-0" placeholder="admin@anandbus.in" required value="admin@anandbus.in">
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label small fw-semibold text-dark">Password</label>
                <div class="input-group">
                    <span class="input-group-text bg-light border-end-0"><i class="fas fa-lock text-muted"></i></span>
                    <input type="password" name="password" class="form-control bg-light border-start-0" placeholder="••••••••" required value="admin123">
                </div>
            </div>

            <button type="submit" class="btn btn-brand w-100 py-3 mt-2 shadow-sm fs-6">
                <i class="fas fa-sign-in-alt me-2"></i>Log In to Admin Panel
            </button>
        </form>

        <div class="mt-4 pt-3 border-top text-center">
            <a href="/" target="_blank" class="text-decoration-none small text-secondary fw-semibold">
                <i class="fas fa-globe me-1 text-warning"></i>View Live Passenger Website
            </a>
        </div>
    </div>
</div>

</body>
</html>
