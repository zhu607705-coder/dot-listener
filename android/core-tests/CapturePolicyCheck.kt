import dev.dotlistener.*
fun main() {
    var assertions=0
    fun verify(ok: Boolean) { check(ok); assertions++ }
    val night=SleepWindow(23*60,7*60)
    for (m in 0..1439) verify(night.contains(m)==(m>=1380 || m<420))
    val policy=CapturePolicy()
    policy.start(true,true,true,false);verify(policy.mode==CaptureMode.RECORDING)
    policy.stop(true);verify(policy.mode==CaptureMode.SLEEP)
    policy.wake();verify(policy.mode==CaptureMode.IDLE)
    verify(runCatching {policy.start(true,true,false,false)}.isFailure)
    verify(runCatching {SleepWindow(0,0)}.isFailure)
    // A normal stop must not be reported as an input failure.
    verify(readWhileRunning({ false }) { error("Read must not start after stop") } == null)
    var running = true
    verify(readWhileRunning({ running }) { running = false; -3 } == null)
    running = true
    verify(readWhileRunning({ running }) { running = false; error("Stopped during read") } == null)
    verify(readWhileRunning({ true }) { 320 } == 320)
    verify(runCatching { readWhileRunning({ true }) { -3 } }.isFailure)
    verify(runCatching { readWhileRunning({ true }) { error("Device failure") } }.isFailure)
    println("Kotlin policy checks passed: $assertions assertions. Android APIs not tested.")
}
