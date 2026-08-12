<?php
/**
 * AnandBus Admin — Routes Management Page (Full CRUD)
 */
require_once __DIR__ . '/check_access.php';

require_access(['super_admin', 'manager']);

$user_role = $_SESSION['role'] ?? 'manager';
$user_data = get_current_user_data();

// Sample Routes Data
$routes_list = [
    [
        'id' => 1,
        'route_code' => 'R-101',
        'start_location' => 'Anand Bus Stand',
        'end_location' => 'Vallabh Vidyanagar',
        'distance_km' => 6.50
    ],
    [
        'id' => 2,
        'route_code' => 'R-102',
        'start_location' => 'Anand Railway Station',
        'end_location' => 'Karamsad Town',
        'distance_km' => 8.20
    ],
    [
        'id' => 3,
        'route_code' => 'R-103',
        'start_location' => 'GIDC Phase 1',
        'end_location' => 'Boriavi Square',
        'distance_km' => 12.00
    ]
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Routes Management — AnandBus Admin</title>
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
                <h4 class="fw-bold mb-0 text-dark"><i class="fas fa-route me-2 text-primary"></i>Routes Management</h4>
                <small class="text-muted">Define route codes, start & end locations, and total distances.</small>
            </div>
            <div class="d-flex align-items-center gap-3">
                <a href="/" target="_blank" class="btn btn-outline-warning text-dark fw-bold rounded-pill px-3 shadow-sm d-flex align-items-center gap-2">
                    <i class="fas fa-globe"></i>
                    <span>View Website</span>
                </a>
                <button class="btn btn-primary rounded-pill px-4 fw-semibold" data-bs-toggle="modal" data-bs-target="#addRouteModal">
                    <i class="fas fa-plus me-2"></i>Add New Route
                </button>
            </div>
        </div>

        <!-- Routes Table -->
        <div class="card card-custom bg-white overflow-hidden">
            <div class="table-responsive">
                <table class="table align-middle mb-0 table-hover">
                    <thead>
                        <tr>
                            <th>Route ID</th>
                            <th>Route Code</th>
                            <th>Start Location</th>
                            <th>End Location</th>
                            <th>Distance</th>
                            <th class="text-end">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($routes_list as $rt): ?>
                        <tr>
                            <td class="fw-bold">#RT-<?php echo sprintf('%03d', $rt['id']); ?></td>
                            <td><span class="badge bg-primary px-3 py-2 fs-7"><?php echo htmlspecialchars($rt['route_code']); ?></span></td>
                            <td class="fw-bold text-dark"><?php echo htmlspecialchars($rt['start_location']); ?></td>
                            <td class="fw-bold text-dark"><?php echo htmlspecialchars($rt['end_location']); ?></td>
                            <td><i class="fas fa-road me-1 text-muted"></i><?php echo $rt['distance_km']; ?> km</td>
                            <td class="text-end">
                                <div class="btn-group">
                                    <button class="btn btn-sm btn-outline-primary" onclick="editRoute(<?php echo $rt['id']; ?>)"><i class="fas fa-edit"></i> Edit</button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="deleteRoute(<?php echo $rt['id']; ?>)"><i class="fas fa-trash-alt"></i> Delete</button>
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

<!-- Modal: Add Route -->
<div class="modal fade" id="addRouteModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0">
            <div class="modal-header border-0 pb-0">
                <h5 class="fw-bold modal-title"><i class="fas fa-route me-2 text-primary"></i>Add New Route</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body p-4">
                <form onsubmit="event.preventDefault(); alert('Route added!'); location.reload();">
                    <div class="mb-3"><label class="form-label">Route Code</label><input type="text" class="form-control" placeholder="R-10X" required></div>
                    <div class="mb-3"><label class="form-label">Start Location</label><input type="text" class="form-control" placeholder="e.g. Anand Bus Stand" required></div>
                    <div class="mb-3"><label class="form-label">End Location</label><input type="text" class="form-control" placeholder="e.g. Vallabh Vidyanagar" required></div>
                    <div class="mb-3"><label class="form-label">Distance (km)</label><input type="number" step="0.1" class="form-control" placeholder="8.5" required></div>
                    <button type="submit" class="btn btn-primary w-100 rounded-3 py-2 fw-bold">Create Route</button>
                </form>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/bootstrap.bundle.min.js"></script>
<script>
function editRoute(id) { alert('Editing Route #' + id); }
function deleteRoute(id) { if (confirm('Delete Route #' + id + '?')) alert('Deleted'); }
</script>
</body>
</html>
