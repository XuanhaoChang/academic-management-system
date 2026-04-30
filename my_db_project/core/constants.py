class RoleType:
    ADMIN = 1
    TEACHER = 2
    STUDENT = 3


class CourseStatus:
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FULL = "FULL"


class ActionType:
    LOGIN = "LOGIN"
    REGISTER = "REGISTER"
    LOGOUT = "LOGOUT"
    CREATE_USER = "CREATE_USER"
    UPDATE_PASSWORD = "UPDATE_PASSWORD"
    UPDATE_USER = "UPDATE_USER"
    IMPORT_USERS = "IMPORT_USERS"
    SOFT_DELETE_USER = "SOFT_DELETE_USER"
    CREATE_DEPT = "CREATE_DEPT"
    UPDATE_DEPT = "UPDATE_DEPT"
    SOFT_DELETE_DEPT = "SOFT_DELETE_DEPT"
    CREATE_MAJOR = "CREATE_MAJOR"
    UPDATE_MAJOR = "UPDATE_MAJOR"
    SOFT_DELETE_MAJOR = "SOFT_DELETE_MAJOR"
    CREATE_COURSE = "CREATE_COURSE"
    UPDATE_COURSE = "UPDATE_COURSE"
    SOFT_DELETE_COURSE = "SOFT_DELETE_COURSE"
    CREATE_TEACHING = "CREATE_TEACHING"
    UPDATE_TEACHING = "UPDATE_TEACHING"
    SOFT_DELETE_TEACHING = "SOFT_DELETE_TEACHING"
    BATCH_ENTER_GRADES  = "BATCH_ENTER_GRADES"
    ARCHIVE_GRADES      = "ARCHIVE_GRADES"
    SUBMIT_GRADES       = "SUBMIT_GRADES"
    SAVE_DAILY_RECORDS  = "SAVE_DAILY_RECORDS"
    IMPORT_GRADES_EXCEL = "IMPORT_GRADES_EXCEL"
    REQUEST_RESCHEDULE  = "REQUEST_RESCHEDULE"
    APPROVE_RESCHEDULE  = "APPROVE_RESCHEDULE"
    REJECT_RESCHEDULE   = "REJECT_RESCHEDULE"
    APPROVE_EXAM_DEFER  = "APPROVE_EXAM_DEFER"
    REJECT_EXAM_DEFER   = "REJECT_EXAM_DEFER"


# GPA 换算表（4.0 制），按分数由高到低排列
# 每项: (最低分数线, 绩点, 等级字母)
GPA_SCALE: list[tuple[float, float, str]] = [
    (90.0, 4.0, "A"),
    (80.0, 3.0, "B"),
    (70.0, 2.0, "C"),
    (60.0, 1.0, "D"),
    (0.0,  0.0, "F"),
]

PASS_SCORE: float = 60.0


def score_to_gpa(score: float) -> tuple[float, str, bool]:
    """将百分制成绩换算为绩点、等级字母和是否通过。"""
    for threshold, gpa, letter in GPA_SCALE:
        if score >= threshold:
            return gpa, letter, score >= PASS_SCORE
    return 0.0, "F", False
