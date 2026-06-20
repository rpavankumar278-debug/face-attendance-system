-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 18, 2025 at 10:05 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `faceatt`
--

-- --------------------------------------------------------

--
-- Table structure for table `tbladminlogin`
--

CREATE TABLE `tbladminlogin` (
  `id` int(11) NOT NULL,
  `userid` varchar(100) NOT NULL,
  `password` varchar(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tbladminlogin`
--

INSERT INTO `tbladminlogin` (`id`, `userid`, `password`) VALUES
(1, 'admin1@gmail.com', '$2b$12$/wzuaB1aCVqLnAnjmrL9p.TUEb22tS/7WvuFqwb.7bMHKuvQdGEDG');

-- --------------------------------------------------------

--
-- Table structure for table `tblattendance`
--

CREATE TABLE `tblattendance` (
  `id` int(11) NOT NULL,
  `sid` varchar(20) NOT NULL,
  `date` date NOT NULL,
  `time` time NOT NULL,
  `subject` varchar(100) NOT NULL,
  `faculty_id` varchar(100) NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `day_of_week` varchar(100) NOT NULL,
  `status` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tblattendance`
--

INSERT INTO `tblattendance` (`id`, `sid`, `date`, `time`, `subject`, `faculty_id`, `start_time`, `end_time`, `day_of_week`, `status`) VALUES
(1, 'S1', '2025-04-19', '01:11:20', 'Data Structure', 'Praveen', '01:00:00', '02:00:00', 'Saturday', 'present');

-- --------------------------------------------------------

--
-- Table structure for table `tblcourse`
--

CREATE TABLE `tblcourse` (
  `id` int(11) NOT NULL,
  `course` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tblcourse`
--

INSERT INTO `tblcourse` (`id`, `course`) VALUES
(1, 'BE (Computer Science)');

-- --------------------------------------------------------

--
-- Table structure for table `tblfaculty`
--

CREATE TABLE `tblfaculty` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `mobile` varchar(20) NOT NULL,
  `emailid` varchar(100) NOT NULL,
  `department` varchar(100) NOT NULL,
  `password` varchar(50) NOT NULL,
  `fid` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tblfaculty`
--

INSERT INTO `tblfaculty` (`id`, `name`, `mobile`, `emailid`, `department`, `password`, `fid`) VALUES
(1, 'Praveen', '9876543210', 'praveen@gmail.com', 'Computer Science', '12345678', 'F1');

-- --------------------------------------------------------

--
-- Table structure for table `tblfacultysubject`
--

CREATE TABLE `tblfacultysubject` (
  `id` int(11) NOT NULL,
  `faculty` varchar(100) NOT NULL,
  `course` varchar(100) NOT NULL,
  `sem` varchar(10) NOT NULL,
  `subject` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tblfacultysubject`
--

INSERT INTO `tblfacultysubject` (`id`, `faculty`, `course`, `sem`, `subject`) VALUES
(1, 'Praveen', 'BE (Computer Science)', 'I', 'Data Structure');

-- --------------------------------------------------------

--
-- Table structure for table `tblinternalmarks`
--

CREATE TABLE `tblinternalmarks` (
  `id` int(11) NOT NULL,
  `student_id` varchar(20) NOT NULL,
  `student_name` varchar(100) NOT NULL,
  `course` varchar(100) NOT NULL,
  `sem` varchar(10) NOT NULL,
  `subject` varchar(100) NOT NULL,
  `internal_exam` varchar(10) NOT NULL,
  `marks` int(11) NOT NULL,
  `total_marks` int(11) NOT NULL,
  `faculty` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tblinternalmarks`
--

INSERT INTO `tblinternalmarks` (`id`, `student_id`, `student_name`, `course`, `sem`, `subject`, `internal_exam`, `marks`, `total_marks`, `faculty`, `created_at`, `updated_at`) VALUES
(1, 'S1', 'Chinni', 'BE (Computer Science)', 'I', 'Data Structure', 'I', 19, 20, 'Praveen', '2025-04-18 19:37:54', '2025-04-18 19:37:54');

-- --------------------------------------------------------

--
-- Table structure for table `tblsem`
--

CREATE TABLE `tblsem` (
  `id` int(11) NOT NULL,
  `sem` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tblsem`
--

INSERT INTO `tblsem` (`id`, `sem`) VALUES
(1, 'I'),
(2, 'II'),
(3, 'III'),
(4, 'IV'),
(5, 'V'),
(6, 'VI'),
(7, 'VII'),
(8, 'VIII');

-- --------------------------------------------------------

--
-- Table structure for table `tblstudents`
--

CREATE TABLE `tblstudents` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `mobile` varchar(20) NOT NULL,
  `emailid` varchar(100) NOT NULL,
  `course` varchar(100) NOT NULL,
  `sem` varchar(20) NOT NULL,
  `password` varchar(50) NOT NULL,
  `sid` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tblstudents`
--

INSERT INTO `tblstudents` (`id`, `name`, `mobile`, `emailid`, `course`, `sem`, `password`, `sid`) VALUES
(1, 'Chinni', '9876543211', 'chinni@gmail.com', 'BE (Computer Science)', 'I', '12345678', 'S1');

-- --------------------------------------------------------

--
-- Table structure for table `tblsubject`
--

CREATE TABLE `tblsubject` (
  `id` int(11) NOT NULL,
  `course` varchar(100) NOT NULL,
  `sem` varchar(20) NOT NULL,
  `Subject` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tblsubject`
--

INSERT INTO `tblsubject` (`id`, `course`, `sem`, `Subject`) VALUES
(2, 'BE (Computer Science)', 'I', 'Data Structure');

-- --------------------------------------------------------

--
-- Table structure for table `tbltimetable`
--

CREATE TABLE `tbltimetable` (
  `id` int(11) NOT NULL,
  `faculty_id` varchar(100) NOT NULL,
  `course` varchar(100) NOT NULL,
  `sem` varchar(10) NOT NULL,
  `subject` varchar(100) NOT NULL,
  `day_of_week` varchar(50) NOT NULL,
  `start_time` varchar(50) NOT NULL,
  `end_time` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tbltimetable`
--

INSERT INTO `tbltimetable` (`id`, `faculty_id`, `course`, `sem`, `subject`, `day_of_week`, `start_time`, `end_time`) VALUES
(2, 'Praveen', 'BE (Computer Science)', 'I', 'Data Structure', 'Saturday', '01:00', '02:00');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `tbladminlogin`
--
ALTER TABLE `tbladminlogin`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tblattendance`
--
ALTER TABLE `tblattendance`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tblcourse`
--
ALTER TABLE `tblcourse`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tblfaculty`
--
ALTER TABLE `tblfaculty`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tblfacultysubject`
--
ALTER TABLE `tblfacultysubject`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tblinternalmarks`
--
ALTER TABLE `tblinternalmarks`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tblsem`
--
ALTER TABLE `tblsem`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tblstudents`
--
ALTER TABLE `tblstudents`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tblsubject`
--
ALTER TABLE `tblsubject`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tbltimetable`
--
ALTER TABLE `tbltimetable`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `tbladminlogin`
--
ALTER TABLE `tbladminlogin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `tblattendance`
--
ALTER TABLE `tblattendance`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `tblcourse`
--
ALTER TABLE `tblcourse`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `tblfaculty`
--
ALTER TABLE `tblfaculty`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `tblfacultysubject`
--
ALTER TABLE `tblfacultysubject`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `tblinternalmarks`
--
ALTER TABLE `tblinternalmarks`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `tblsem`
--
ALTER TABLE `tblsem`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `tblstudents`
--
ALTER TABLE `tblstudents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `tblsubject`
--
ALTER TABLE `tblsubject`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `tbltimetable`
--
ALTER TABLE `tbltimetable`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
