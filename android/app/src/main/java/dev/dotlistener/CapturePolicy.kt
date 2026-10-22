package dev.dotlistener

/** Pure policy shared by the service and JVM checks. A wake event never starts audio. */
data class SleepWindow(val start: Int, val end: Int) {
    init { require(start in 0..1439 && end in 0..1439 && start != end) }
    fun contains(minute: Int): Boolean {
        require(minute in 0..1439)
        return if (start < end) minute >= start && minute < end else minute >= start || minute < end
    }
}
enum class CaptureMode { IDLE, RECORDING, PAUSED, SLEEP, INTERRUPTED }
class CapturePolicy {
    var mode: CaptureMode = CaptureMode.IDLE
        private set
    fun start(consent: Boolean, permission: Boolean, visibleAction: Boolean, sleeping: Boolean) {
        require(consent && permission && visibleAction && !sleeping)
        mode = CaptureMode.RECORDING
    }
    fun stop(sleeping: Boolean = false) { mode = if (sleeping) CaptureMode.SLEEP else CaptureMode.PAUSED }
    fun interrupt() { mode = CaptureMode.INTERRUPTED }
    fun wake() { mode = CaptureMode.IDLE }
}

/** Stop can unblock AudioRecord.read with an error code or exception. */
fun readWhileRunning(isRunning: () -> Boolean, read: () -> Int): Int? {
    if (!isRunning()) return null
    val count = try { read() } catch (e: Exception) {
        if (!isRunning()) return null
        throw e
    }
    if (!isRunning()) return null
    check(count > 0) { "Audio input unavailable: $count" }
    return count
}
