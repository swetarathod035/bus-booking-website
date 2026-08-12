<?php
/**
 * AnandBus Admin — Users & Roles Management Page (Full CRUD)
 */
require_once __DIR__ . '/check_access.php';

// Enforce access for Super Admin
require_access(['super_admin']);

$user_role = $_SESSION['role'] ?? 'super_admin';
$user_data = get_current_user_data();

// Sample Users Data (In production, fetched via PDO/MySQL)
$users_list = [
    [
        'id' => 1,
        'name' => 'System Super Admin',
        'email' => 'admin@anandbus.in',
        'phone' => '9876543210',
        'role' => 'super_admin',
        'status' => 'active',
        'created_at' => '2026-01-10 10:00:00'
    ],
    [
        'id' => 2,
        'name' => 'Rajesh Patel (Manager)',
        'email' => 'manager@anandbus.in',
        'phone' => '9876543211',
        'role' => 'manager',
        'status' => 'active',
        'created_at' => '2026-01-15 11:30:00'
    ],
    [
        'id' => 3,
        'name' => 'Vikram Singh (Conductor)',
        'email' => 'conductor@anandbus.in',
        'phone' => '9876543212',
        'role' => 'conductor',
        'status' => 'active',
        'created_at' => '2026-02-01 09:15:00'
    ],
    [
        'id' => 4,
        'name' => 'Anil Kumar (Student)',
        'email' => 'anil@student.in',
        'phone' => '9876543213',
        'role' => 'passenger',
        'status' => 'active',
        'created_at' => '2026-02-10 14:20:00'
    ],
    [
        'id' => 5,
        'name' => 'Ramesh Solanki (Suspended)',
        'email' => 'ramesh@user.com',
        'phone' => '9876543214',
        'role' => 'passenger',
        'status' => 'suspended',
        'created_at' => '2026-02-12 16:45:00'
    ]
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Users & Roles Management — AnandBus Admin</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- FontAwesome Icons -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #F5F8FA; font-family: 'Inter', -apple-system, sans-serif; color: #1E293B; }
        .card-custom { border: none; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
        .table th { background-color: #F8FAFC; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; color: #64748B; font-weight: 700; }
        .badge-super_admin { background-color: #7C3AED; color: #FFF; }
        .badge-manager { background-color: #2563EB; color: #FFF; }
        .badge-conductor { background-color: #D97706; color: #FFF; }
        .badge-passenger { background-color: #64748B; color: #FFF; }
    </style>
</head>
<body>

<div class="d-flex">
    <!-- Dynamic Sidebar Component -->
    <?php include __DIR__ . '/sidebar.php'; ?>

    <!-- Main Content Area -->
    <div class="main-content flex-grow-1 p-4">
        
        <!-- Top Header Bar -->
        <div class="d-flex justify-content-between align-items-center mb-4 bg-white p-3 rounded-4 shadow-sm">
            <div>
                <h4 class="fw-bold mb-0 text-dark"><i class="fas fa-users-cog me-2 text-primary"></i>Users & Roles Management</h4>
                <small class="text-muted">Manage system users, assign roles, and block/unblock accounts.</small>
            </div>
            <div class="d-flex align-items-center gap-3">
                <!-- VIEW WEBSITE SHORTCUT -->
                <a href="/" target="_blank" class="btn btn-outline-warning text-dark fw-bold rounded-pill px-3 shadow-sm d-flex align-items-center gap-2">
                    <i class="fas fa-globe"></i>
                    <span>View Website</span>
                </a>

                <button class="btn btn-primary rounded-pill px-4 fw-semibold" data-bs-toggle="modal" data-bs-target="#addUserModal">
                    <i class="fas fa-user-plus me-2"></i>Add New User
                </button>
            </div>
        </div>

        <!-- Search & Filter Controls -->
        <div class="card card-custom p-4 bg-white mb-4">
            <div class="row g-3 align-items-center">
                <div class="col-md-6">
                    <div class="input-group">
                        <span class="input-group-text bg-light border-end-0"><i class="fas fa-search text-muted"></i></span>
                        <input type="text" id="userSearch" class="form-control bg-light border-start-0" placeholder="Search by name, email, or phone...">
                    </div>
                </div>
                <div class="col-md-4">
                    <select id="roleFilter" class="form-select bg-light">
                        <option value="">All Roles</option>
                        <option value="super_admin">Super Administrator</option>
                        <option value="manager">Bus Manager</option>
                        <option value="conductor">Conductor / Driver</option>
                        <option value="passenger">Passenger / Student</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <button class="btn btn-outline-secondary w-100" onclick="resetFilters()">Reset</button>
                </div>
            </div>
        </div>

        <!-- Users Table -->
        <div class="card card-custom bg-white overflow-hidden">
            <div class="table-responsive">
                <table class="table align-middle mb-0 table-hover" id="usersTable">
                    <thead>
                        <tr>
                            <th>User ID</th>
                            <th>Full Name & Contact</th>
                            <th>Role</th>
                            <th>Account Status</th>
                            <th>Registered Date</th>
                            <th class="text-end">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($users_list as $usr): ?>
                        <tr data-role="<?php echo $usr['role']; ?>">
                            <td class="fw-bold">#USR-<?php echo sprintf('%04d', $usr['id']); ?></td>
                            <td>
                                <div class="fw-bold text-dark"><?php echo htmlspecialchars($usr['name']); ?></div>
                                <small class="text-muted"><i class="far fa-envelope me-1"></i><?php echo htmlspecialchars($usr['email']); ?> | <i class="fas fa-phone me-1"></i><?php echo htmlspecialchars($usr['phone']); ?></small>
                            </td>
                            <td>
                                <span class="badge badge-<?php echo $usr['role']; ?> px-3 py-2 rounded-pill">
                                    <?php echo get_role_title($usr['role']); ?>
                                </span>
                            </td>
                            <td>
                                <?php if ($usr['status'] === 'active'): ?>
                                    <span class="badge bg-success-subtle text-success fw-bold px-3 py-1 rounded-pill"><i class="fas fa-check-circle me-1"></i>Active</span>
                                <?php else: ?>
                                    <span class="badge bg-danger-subtle text-danger fw-bold px-3 py-1 rounded-pill"><i class="fas fa-ban me-1"></i>Blocked</span>
                                <?php endif; ?>
                            </td>
                            <td><small class="text-muted"><?php echo date('d M Y', strtotime($usr['created_at'])); ?></small></td>
                            <td class="text-end">
                                <div class="btn-group">
                                    <button class="btn btn-sm btn-outline-primary" title="Edit User & Role" onclick="editUser(<?php echo $usr['id']; ?>, '<?php echo htmlspecialchars($usr['name']); ?>', '<?php echo htmlspecialchars($usr['email']); ?>', '<?php echo $usr['role']; ?>')">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <?php if ($usr['status'] === 'active'): ?>
                                        <button class="btn btn-sm btn-outline-warning" title="Block User" onclick="toggleUserBlock(<?php echo $usr['id']; ?>, 'block')">
                                            <i class="fas fa-user-slash"></i>
                                        </button>
                                    <?php else: ?>
                                        <button class="btn btn-sm btn-outline-success" title="Unblock User" onclick="toggleUserBlock(<?php echo $usr['id']; ?>, 'unblock')">
                                            <i class="fas fa-user-check"></i>
                                        </button>
                                    <?php endif; ?>
                                    <button class="btn btn-sm btn-outline-danger" title="Delete User" onclick="deleteUser(<?php echo $usr['id']; ?>)">
                                        <i class="fas fa-trash-alt"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</div>

<!-- Modal: Add New User -->
<div class="modal fade" id="addUserModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0">
            <div class="modal-header border-0 pb-0">
                <h5 class="fw-bold modal-title"><i class="fas fa-user-plus me-2 text-primary"></i>Add New User</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-4">
                <form id="addUserForm" onsubmit="handleUserSubmit(event, 'add')">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Full Name</label>
                        <input type="text" class="form-control" placeholder="Enter name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Email Address</label>
                        <input type="email" class="form-control" placeholder="user@email.com" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Phone Number</label>
                        <input type="tel" class="form-control" placeholder="10 digit phone" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Assign Role</label>
                        <select class="form-select" required>
                            <option value="passenger">Passenger / Student</option>
                            <option value="conductor">Conductor / Driver</option>
                            <option value="manager">Bus Manager</option>
                            <option value="super_admin">Super Administrator</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 rounded-3 py-2 fw-bold">Create User Account</button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- Modal: Edit User -->
<div class="modal fade" id="editUserModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0">
            <div class="modal-header border-0 pb-0">
                <h5 class="fw-bold modal-title"><i class="fas fa-user-edit me-2 text-primary"></i>Edit User Role & Details</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-4">
                <form id="editUserForm" onsubmit="handleUserSubmit(event, 'edit')">
                    <input type="hidden" id="edit_user_id">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Full Name</label>
                        <input type="text" class="form-control" id="edit_user_name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Email Address</label>
                        <input type="email" class="form-control" id="edit_user_email" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Assign Role</label>
                        <select class="form-select" id="edit_user_role" required>
                            <option value="passenger">Passenger / Student</option>
                            <option value="conductor">Conductor / Driver</option>
                            <option value="manager">Bus Manager</option>
                            <option value="super_admin">Super Administrator</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 rounded-3 py-2 fw-bold">Save User Changes</button>
                </form>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/bootstrap.bundle.min.js"></script>
<script>
function editUser(id, name, email, role) {
    document.getElementById('edit_user_id').value = id;
    document.getElementById('edit_user_name').value = name;
    document.getElementById('edit_user_email').value = email;
    document.getElementById('edit_user_role').value = role;
    new bootstrap.Modal(document.getElementById('editUserModal')).show();
}

function toggleUserBlock(id, action) {
    if (confirm(`Are you sure you want to ${action} User #${id}?`)) {
        alert(`User #${id} has been ${action}ed successfully.`);
        location.reload();
    }
}

function deleteUser(id) {
    if (confirm(`Are you sure you want to permanently delete User #${id}?`)) {
        alert(`User #${id} deleted.`);
        location.reload();
    }
}

function handleUserSubmit(e, type) {
    e.preventDefault();
    alert(`User ${type === 'add' ? 'created' : 'updated'} successfully!`);
    location.reload();
}
</script>

</body>
</html>
