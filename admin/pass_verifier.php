<?php
/**
 * AnandBus Admin — Mobile-Optimized Conductor Pass Verifier Tool
 */
require_once __DIR__ . '/check_access.php';

require_access(['super_admin', 'manager', 'conductor']);

$user_role = $_SESSION['role'] ?? 'conductor';
$user_data = get_current_user_data();

$search_query = $_GET['q'] ?? '';
$verification_result = null;

if ($search_query) {
    // Sample Database Verification Logic
    if (stristr($search_query, 'STU-2026-9011') || stristr($search_query, '9011') || stristr($search_query, 'pooja')) {
        $verification_result = [
            'status' => 'ACTIVE',
            'status_class' => 'bg-success',
            'pass_id' => 'STU-2026-9011',
            'passenger_name' => 'Pooja Shah',
            'pass_type' => 'Quarterly Student Pass',
            'valid_until' => '2026-04-30',
            'college' => 'NV Patel College of Pure & Applied Sciences',
            'photo' => 'images/sample_avatar.jpg'
        ];
    } elseif (stristr($search_query, 'EXPIRED') || stristr($search_query, '7810')) {
        $verification_result = [
            'status' => 'EXPIRED',
            'status_class' => 'bg-warning text-dark',
            'pass_id' => 'STU-2026-7810',
            'passenger_name' => 'Rahul Parmar',
            'pass_type' => 'Monthly Student Pass',
            'valid_until' => '2026-01-31',
            'college' => 'Sardar Patel University',
            'photo' => 'images/sample_avatar.jpg'
        ];
    } else {
        $verification_result = [
            'status' => 'INVALID',
            'status_class' => 'bg-danger',
            'message' => 'No active student pass or booking ticket found matching code: ' . htmlspecialchars($search_query)
        ];
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pass Verifier Tool — AnandBus Conductor</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #0F172A; font-family: 'Inter', -apple-system, sans-serif; color: #F8FAFC; min-height: 100vh; }
        .verifier-card { background: #1E293B; border-radius: 24px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
    </style>
</head>
<body>

<div class="container py-4" style="max-width: 540px;">
    
    <!-- Top Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div class="d-flex align-items-center gap-2">
            <div class="bg-primary p-2 rounded-3 text-white"><i class="fas fa-qrcode fs-4"></i></div>
            <div>
                <h5 class="fw-bold mb-0 text-white">AnandBus Verifier</h5>
                <small class="text-white-50">Conductor & Staff Scanner</small>
            </div>
        </div>

        <a href="/" target="_blank" class="btn btn-sm btn-outline-warning rounded-pill px-3">
            <i class="fas fa-globe me-1"></i>Website
        </a>
    </div>

    <!-- Verifier Input Box Card -->
    <div class="verifier-card p-4 mb-4">
        <h6 class="fw-bold text-white mb-3"><i class="fas fa-search me-2 text-warning"></i>Scan or Type Pass ID / QR Code Hash</h6>
        
        <form method="GET" action="pass_verifier.php">
            <div class="input-group input-group-lg mb-3">
                <span class="input-group-text bg-dark border-secondary text-white-50"><i class="fas fa-barcode"></i></span>
                <input type="text" name="q" class="form-control bg-dark text-white border-secondary fs-6" placeholder="e.g. STU-2026-9011" value="<?php echo htmlspecialchars($search_query); ?>" autofocus required>
            </div>
            
            <button type="submit" class="btn btn-warning w-100 py-3 rounded-3 fw-bold text-dark fs-6 shadow">
                <i class="fas fa-shield-alt me-2"></i>Verify Pass Status
            </button>
        </form>
    </div>

    <!-- Verification Result Card -->
    <?php if ($verification_result): ?>
    <div class="verifier-card p-4 text-center">
        <span class="badge <?php echo $verification_result['status_class']; ?> px-4 py-2 rounded-pill fs-5 mb-3">
            <?php echo $verification_result['status']; ?> PASS
        </span>

        <?php if ($verification_result['status'] === 'INVALID'): ?>
            <div class="text-danger my-3"><i class="fas fa-times-circle fa-4x"></i></div>
            <p class="text-white-50"><?php echo $verification_result['message']; ?></p>
        <?php else: ?>
            <div class="my-2">
                <i class="fas fa-user-circle fa-4x text-info mb-2"></i>
                <h4 class="fw-bold text-white mb-1"><?php echo htmlspecialchars($verification_result['passenger_name']); ?></h4>
                <div class="badge bg-secondary mb-3"><?php echo htmlspecialchars($verification_result['pass_id']); ?></div>
            </div>

            <div class="bg-dark p-3 rounded-3 text-start small mb-3">
                <div class="d-flex justify-content-between py-1 border-bottom border-secondary">
                    <span class="text-white-50">Pass Type</span>
                    <span class="fw-bold text-white"><?php echo htmlspecialchars($verification_result['pass_type']); ?></span>
                </div>
                <div class="d-flex justify-content-between py-1 border-bottom border-secondary">
                    <span class="text-white-50">Valid Until</span>
                    <span class="fw-bold text-success"><?php echo htmlspecialchars($verification_result['valid_until']); ?></span>
                </div>
                <div class="d-flex justify-content-between py-1">
                    <span class="text-white-50">Institution</span>
                    <span class="fw-bold text-white text-truncate" style="max-width:200px;"><?php echo htmlspecialchars($verification_result['college']); ?></span>
                </div>
            </div>
        <?php endif; ?>
    </div>
    <?php endif; ?>

</div>

</body>
</html>
