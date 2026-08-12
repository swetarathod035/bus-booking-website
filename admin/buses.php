<?php
/**
 * AnandBus Admin — Buses Management Page (Full CRUD)
 */
require_once __DIR__ . '/check_access.php';

require_access(['super_admin', 'manager']);

$user_role = $_SESSION['role'] ?? 'manager';
$user_data = get_current_user_data();

// Sample Buses Data
$buses_list = [
    [
        'id' => 1,
        'bus_number' => 'GJ-23-AB-1001',
        'operator_name' => 'Anand Urban Transport',
        'capacity' => 45,
        'bus_type' => 'Electric AC Express',
        'status' => 'active'
    ],
    [
        'id' => 2,
        'bus_number' => 'GJ-23-AB-1002',
        'operator_name' => 'Anand Urban Transport',
        'capacity' => 40,
        'bus_type' => 'Non-AC Deluxe',
        'status' => 'active'
    ],
    [
        'id' => 3,
        'bus_number' => 'GJ-23-AB-1003',
        'operator_name' => 'Anand Express Fleet',
        'capacity' => 50,
        'bus_type' => 'City Mini Bus',
        'status' => 'maintenance'
    ]
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buses Management — AnandBus Admin</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #F5F8FA; font-family: 'Inter', -apple-system, sans-serif; color: #1E293B; }
        .card-custom { border: none; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
        .table th { background-color: #F8FAFC; text-transform: uppercase; font-size: 0.75rem; color: #64748B; font-weight: 700; }
    </style>
</head>
<body>

<div class="d-flex">
    <?php include __DIR__ . '/sidebar.php'; ?>

    <div class="main-content flex-grow-1 p-4">
        <div class="d-flex justify-content-between align-items-center mb-4 bg-white p-3 rounded-4 shadow-sm">
            <div>
                <h4 class="fw-bold mb-0 text-dark"><i class="fas fa-bus me-2 text-primary"></i>Bus Fleet Management</h4>
                <small class="text-muted">Add new buses, update capacity, type, and maintenance status.</small>
            </div>
            <div class="d-flex align-items-center gap-3">
                <a href="/" target="_blank" class="btn btn-outline-warning text-dark fw-bold rounded-pill px-3 shadow-sm d-flex align-items-center gap-2">
                    <i class="fas fa-globe"></i>
                    <span>View Website</span>
                </a>
                <button class="btn btn-primary rounded-pill px-4 fw-semibold" data-bs-toggle="modal" data-bs-target="#addBusModal">
                    <i class="fas fa-plus me-2"></i>Add New Bus
                </button>
            </div>
        </div>

        <!-- Buses Table -->
        <div class="card card-custom bg-white overflow-hidden">
            <div class="table-responsive">
                <table class="table align-middle mb-0 table-hover">
                    <thead>
                        <tr>
                            <th>Bus ID</th>
                            <th>Bus Number</th>
                            <th>Operator Name</th>
                            <th>Seating Capacity</th>
                            <th>Bus Type</th>
                            <th>Status</th>
                            <th class="text-end">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($buses_list as $bus): ?>
                        <tr>
                            <td class="fw-bold">#BUS-<?php echo sprintf('%03d', $bus['id']); ?></td>
                            <td class="fw-bold text-dark"><?php echo htmlspecialchars($bus['bus_number']); ?></td>
                            <td><?php echo htmlspecialchars($bus['operator_name']); ?></td>
                            <td><i class="fas fa-couch me-1 text-muted"></i><?php echo $bus['capacity']; ?> Seats</td>
                            <td><span class="badge bg-light text-dark border"><?php echo htmlspecialchars($bus['bus_type']); ?></span></td>
                            <td>
                                <?php if ($bus['status'] === 'active'): ?>
                                    <span class="badge bg-success px-3 py-1 rounded-pill">Active</span>
                                <?php else: ?>
                                    <span class="badge bg-warning text-dark px-3 py-1 rounded-pill">Maintenance</span>
                                <?php endif; ?>
                            </td>
                            <td class="text-end">
                                <div class="btn-group">
                                    <button class="btn btn-sm btn-outline-primary" onclick="editBus(<?php echo $bus['id']; ?>)"><i class="fas fa-edit"></i> Edit</button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="deleteBus(<?php echo $bus['id']; ?>)"><i class="fas fa-trash-alt"></i> Delete</button>
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

<!-- Modal: Add Bus -->
<div class="modal fade" id="addBusModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0">
            <div class="modal-header border-0 pb-0">
                <h5 class="fw-bold modal-title"><i class="fas fa-bus me-2 text-primary"></i>Add New Bus</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body p-4">
                <form onsubmit="event.preventDefault(); alert('Bus added!'); location.reload();">
                    <div class="mb-3"><label class="form-label">Bus Number</label><input type="text" class="form-control" placeholder="GJ-23-XX-0000" required></div>
                    <div class="mb-3"><label class="form-label">Capacity</label><input type="number" class="form-control" value="40" required></div>
                    <div class="mb-3"><label class="form-label">Bus Type</label><input type="text" class="form-control" placeholder="Express AC / Sleeper" required></div>
                    <button type="submit" class="btn btn-primary w-100 rounded-3 py-2 fw-bold">Save Bus Details</button>
                </form>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/bootstrap.bundle.min.js"></script>
<script>
function editBus(id) { alert('Editing Bus #' + id); }
function deleteBus(id) { if (confirm('Delete Bus #' + id + '?')) alert('Deleted'); }
</script>
</body>
</html>
