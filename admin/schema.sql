-- ============================================================
-- AnandBus Database Schema (MySQL)
-- ============================================================

CREATE DATABASE IF NOT EXISTS `anandbus_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `anandbus_db`;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL UNIQUE,
  `phone` VARCHAR(20) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `role` ENUM('super_admin', 'manager', 'conductor', 'passenger') NOT NULL DEFAULT 'passenger',
  `status` ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Buses Table
CREATE TABLE IF NOT EXISTS `buses` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bus_number` VARCHAR(50) NOT NULL UNIQUE,
  `operator_name` VARCHAR(100) NOT NULL DEFAULT 'AnandBus Transport Co.',
  `capacity` INT NOT NULL DEFAULT 40,
  `bus_type` VARCHAR(50) NOT NULL DEFAULT 'Express AC',
  `status` ENUM('active', 'maintenance', 'inactive') NOT NULL DEFAULT 'active',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Routes Table
CREATE TABLE IF NOT EXISTS `routes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `route_code` VARCHAR(50) NOT NULL UNIQUE,
  `start_location` VARCHAR(100) NOT NULL,
  `end_location` VARCHAR(100) NOT NULL,
  `distance_km` DECIMAL(6,2) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Bus Stops Table
CREATE TABLE IF NOT EXISTS `bus_stops` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `route_id` INT NOT NULL,
  `stop_name` VARCHAR(100) NOT NULL,
  `stop_order` INT NOT NULL,
  `landmark` VARCHAR(150) DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`route_id`) REFERENCES `routes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Schedules Table
CREATE TABLE IF NOT EXISTS `schedules` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bus_id` INT NOT NULL,
  `route_id` INT NOT NULL,
  `conductor_id` INT DEFAULT NULL,
  `departure_time` TIME NOT NULL,
  `arrival_time` TIME NOT NULL,
  `duration_mins` INT NOT NULL,
  `status` ENUM('On Time', 'Delayed', 'Completed', 'Cancelled') NOT NULL DEFAULT 'On Time',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`bus_id`) REFERENCES `buses`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`route_id`) REFERENCES `routes`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`conductor_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Student Passes Table
CREATE TABLE IF NOT EXISTS `student_passes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `college_name` VARCHAR(150) NOT NULL,
  `student_id_card` VARCHAR(255) NOT NULL,
  `pass_type` VARCHAR(50) NOT NULL DEFAULT 'Monthly Student Pass',
  `status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
  `valid_from` DATE DEFAULT NULL,
  `valid_until` DATE DEFAULT NULL,
  `qr_code_hash` VARCHAR(255) DEFAULT NULL,
  `rejection_reason` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Bookings Table
CREATE TABLE IF NOT EXISTS `bookings` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `schedule_id` INT NOT NULL,
  `seat_number` VARCHAR(10) NOT NULL,
  `fare_amount` DECIMAL(8,2) NOT NULL,
  `payment_status` ENUM('pending', 'paid', 'failed', 'refunded') NOT NULL DEFAULT 'pending',
  `booking_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`schedule_id`) REFERENCES `schedules`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed Sample Super Admin User (Password: admin123 hashed with BCRYPT)
INSERT INTO `users` (`name`, `email`, `phone`, `password`, `role`, `status`) VALUES
('System Super Admin', 'admin@anandbus.in', '9876543210', '$2y$10$e0MYzXyjpJS7Pd0RVvHwHe1T9vW1pG/0o4z9tL/M3Zq5e7u1y5.4S', 'super_admin', 'active'),
('Rajesh Patel (Manager)', 'manager@anandbus.in', '9876543211', '$2y$10$e0MYzXyjpJS7Pd0RVvHwHe1T9vW1pG/0o4z9tL/M3Zq5e7u1y5.4S', 'manager', 'active'),
('Vikram Singh (Conductor)', 'conductor@anandbus.in', '9876543212', '$2y$10$e0MYzXyjpJS7Pd0RVvHwHe1T9vW1pG/0o4z9tL/M3Zq5e7u1y5.4S', 'conductor', 'active');

-- Seed Sample Buses
INSERT INTO `buses` (`bus_number`, `operator_name`, `capacity`, `bus_type`, `status`) VALUES
('GJ-23-AB-1001', 'Anand Urban Transport', 45, 'Electric AC Express', 'active'),
('GJ-23-AB-1002', 'Anand Urban Transport', 40, 'Non-AC Deluxe', 'active'),
('GJ-23-AB-1003', 'Anand Express Fleet', 50, 'City Mini Bus', 'maintenance');

-- Seed Sample Routes
INSERT INTO `routes` (`route_code`, `start_location`, `end_location`, `distance_km`) VALUES
('R-101', 'Anand Bus Stand', 'Vallabh Vidyanagar', 6.50),
('R-102', 'Anand Railway Station', 'Karamsad Town', 8.20),
('R-103', 'GIDC Phase 1', 'Boriavi Square', 12.00);

-- Seed Sample Schedules
INSERT INTO `schedules` (`bus_id`, `route_id`, `conductor_id`, `departure_time`, `arrival_time`, `duration_mins`, `status`) VALUES
(1, 1, 3, '08:00:00', '08:25:00', 25, 'On Time'),
(2, 2, 3, '09:15:00', '09:45:00', 30, 'Delayed'),
(1, 3, 3, '10:30:00', '11:15:00', 45, 'On Time');
