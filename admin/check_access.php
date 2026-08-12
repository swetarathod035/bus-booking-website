<?php
/**
 * AnandBus Admin — Session & Role-Based Access Control (RBAC) Helper
 */

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

/**
 * Check if the user is authenticated.
 */
function is_logged_in() {
    return isset($_SESSION['user_id']) && !empty($_SESSION['user_id']) && isset($_SESSION['role']);
}

/**
 * Get current logged in user details.
 */
function get_current_user_data() {
    if (!is_logged_in()) {
        return null;
    }
    return [
        'id' => $_SESSION['user_id'],
        'name' => $_SESSION['user_name'] ?? 'User',
        'email' => $_SESSION['user_email'] ?? '',
        'role' => $_SESSION['role'] ?? 'passenger',
        'role_title' => get_role_title($_SESSION['role'] ?? 'passenger')
    ];
}

/**
 * Check if user has any of the permitted roles.
 */
function has_role($permitted_roles = []) {
    if (!is_array($permitted_roles)) {
        $permitted_roles = [$permitted_roles];
    }
    if (!is_logged_in()) {
        return false;
    }
    return in_array($_SESSION['role'], $permitted_roles);
}

/**
 * Enforce RBAC middleware check on admin pages.
 */
function require_access($permitted_roles = []) {
    if (!is_logged_in()) {
        header("Location: login.php?error=session_expired");
        exit();
    }

    if (!empty($permitted_roles) && !has_role($permitted_roles)) {
        header("Location: unauthorized.php");
        exit();
    }
}

/**
 * Helper to display human readable role titles.
 */
function get_role_title($role) {
    $roles = [
        'super_admin' => 'Super Administrator',
        'manager' => 'Bus Manager / Operator Staff',
        'conductor' => 'Conductor / Driver',
        'passenger' => 'Passenger / Student'
    ];
    return $roles[$role] ?? 'User';
}
?>
