<?php
/**
 * AnandBus Admin — Student Pass Approval & Verification System
 */
require_once __DIR__ . '/check_access.php';

require_access(['super_admin', 'manager']);

$user_role = $_SESSION['role'] ?? 'manager';
$user_data = get_current_user_data();

// Sample Student Passes Data
$passes_list = [
    [
        'id' => 1001,
        'pass_id' => 'STU-2026-8942',
        'student_name' => 'Anil Patel',
        'college_name' => 'Birla Vishvakarma Mahavidyalaya (BVM)',
        'id_card_img' => 'images/sample_id_card.jpg',
        'pass_type' => 'Monthly Student Pass',
        'status' => 'pending',
        'valid_from' => '2026-03-01',
        'valid_until' => '2026-03-31',
        'qr_code_hash' => 'hash_8942_bvm_anil',
        'applied_date' => '2026-02-12'
    ],
    [
        'id' => 1002,
        'pass_id' => 'STU-2026-9011',
        'student_name' => 'Pooja Shah',
        'college_name' => 'NV Patel College of Pure & Applied Sciences',
        'id_card_img' => 'images/sample_id_card.jpg',
        'pass_type' => 'Quarterly Pass',
        'status' => 'approved',
        'valid_from' => '2026-02-01',
        'valid_until' => '2026-04-30',
        'qr_code_hash' => 'hash_9011_nvp_pooja',
        'applied_date' => '2026-01-28'
    ],
    [
        'id' => 1003,
        'pass_id' => 'STU-2026-7810',
        'student_name' => 'Rahul Parmar',
        'college_name' => 'Sardar Patel University (SPU)',
        'id_card_img' => 'images/sample_id_card.jpg',
        'pass_type' => 'Monthly Student Pass',
        'status' => 'rejected',
        'rejection_reason' => 'Expired College ID Card uploaded',
        'valid_from' => null,
        'valid_until' => null,
        'qr_code_hash' => null,
        'applied_date' => '2026-02-05'
    ]
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Pass Approval System — AnandBus Admin</title>
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
                <h4 class="fw-bold mb-0 text-dark"><i class="fas fa-id-card me-2 text-primary"></i>Student Pass Approval System</h4>
                <small class="text-muted">Review pending applications, inspect ID proofs, and issue digital QR passes.</small>
            </div>
            <div class="d-flex align-items-center gap-3">
                <a href="/" target="_blank" class="btn btn-outline-warning text-dark fw-bold rounded-pill px-3 shadow-sm d-flex align-items-center gap-2">
                    <i class="fas fa-globe"></i>
                    <span>View Website</span>
                </a>
            </div>
        </div>

        <!-- Metric Summary Cards -->
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="card card-custom p-3 bg-white border-start border-warning border-4">
                    <small class="text-muted text-uppercase fw-semibold" style="font-size:0.75rem;">Pending Approval</small>
                    <h3 class="fw-bold mb-0 text-warning">1 Application</h3>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card card-custom p-3 bg-white border-start border-success border-4">
                    <small class="text-muted text-uppercase fw-semibold" style="font-size:0.75rem;">Approved Passes</small>
                    <h3 class="fw-bold mb-0 text-success">3,850 Active</h3>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card card-custom p-3 bg-white border-start border-danger border-4">
                    <small class="text-muted text-uppercase fw-semibold" style="font-size:0.75rem;">Rejected Queue</small>
                    <h3 class="fw-bold mb-0 text-danger">12 Rejected</h3>
                </div>
            </div>
        </div>

        <!-- Student Passes Data Table -->
        <div class="card card-custom bg-white overflow-hidden">
            <div class="table-responsive">
                <table class="table align-middle mb-0 table-hover">
                    <thead>
                        <tr>
                            <th>Pass ID</th>
                            <th>Student Details</th>
                            <th>College / Institution</th>
                            <th>Pass Type</th>
                            <th>Status</th>
                            <th>ID Proof</th>
                            <th class="text-end">Approval Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($passes_list as $pass): ?>
                        <tr>
                            <td class="fw-bold"><?php echo htmlspecialchars($pass['pass_id']); ?></td>
                            <td>
                                <div class="fw-bold text-dark"><?php echo htmlspecialchars($pass['student_name']); ?></div>
                                <small class="text-muted">Applied: <?php echo $pass['applied_date']; ?></small>
                            </td>
                            <td class="fw-semibold text-dark"><?php echo htmlspecialchars($pass['college_name']); ?></td>
                            <td><span class="badge bg-light text-dark border"><?php echo htmlspecialchars($pass['pass_type']); ?></span></td>
                            <td>
                                <?php if ($pass['status'] === 'pending'): ?>
                                    <span class="badge bg-warning text-dark px-3 py-1 rounded-pill"><i class="fas fa-clock me-1"></i>Pending</span>
                                <?php elseif ($pass['status'] === 'approved'): ?>
                                    <span class="badge bg-success px-3 py-1 rounded-pill"><i class="fas fa-check-circle me-1"></i>Approved</span>
                                <?php else: ?>
                                    <span class="badge bg-danger px-3 py-1 rounded-pill"><i class="fas fa-times-circle me-1"></i>Rejected</span>
                                <?php endif; ?>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-outline-secondary rounded-pill" onclick="previewIDCard('<?php echo htmlspecialchars($pass['student_name']); ?>')">
                                    <i class="fas fa-eye me-1"></i>View ID
                                </button>
                            </td>
                            <td class="text-end">
                                <?php if ($pass['status'] === 'pending'): ?>
                                    <button class="btn btn-sm btn-success rounded-pill px-3 me-1 fw-bold" onclick="approvePass(<?php echo $pass['id']; ?>)">
                                        <i class="fas fa-check me-1"></i>Approve
                                    </button>
                                    <button class="btn btn-sm btn-danger rounded-pill px-3 fw-bold" onclick="rejectPass(<?php echo $pass['id']; ?>)">
                                        <i class="fas fa-times me-1"></i>Reject
                                    </button>
                                <?php else: ?>
                                    <small class="text-muted fw-semibold">Processed</small>
                                <?php endif; ?>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<!-- Modal: ID Card Preview -->
<div class="modal fade" id="previewModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0 text-center p-4">
            <h5 class="fw-bold mb-3" id="previewTitle">Student College ID Proof</h5>
            <div class="p-3 bg-light rounded-4 border mb-3">
                <i class="fas fa-id-card-clip fa-5x text-secondary my-3"></i>
                <div class="fw-bold text-dark">Official Student College ID Document</div>
                <small class="text-muted">Verified Document Proof</small>
            </div>
            <button type="button" class="btn btn-secondary rounded-pill w-100" data-bs-dismiss="modal">Close Preview</button>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/bootstrap.bundle.min.js"></script>
<script>
function previewIDCard(name) {
    document.getElementById('previewTitle').textContent = name + "'s College ID Proof";
    new bootstrap.Modal(document.getElementById('previewModal')).show();
}

function approvePass(id) {
    const qrHash = 'QR_ANANDBUS_' + Math.floor(Math.random() * 90000 + 10000);
    alert('Student Pass #' + id + ' Approved successfully!\nGenerated QR Hash: ' + qrHash);
    location.reload();
}

function rejectPass(id) {
    const reason = prompt('Please enter reason for rejection:', 'Invalid / Expired College ID document');
    if (reason) {
        alert('Pass #' + id + ' Rejected. Reason: ' + reason);
        location.reload();
    }
}
</script>
</body>
</html>
