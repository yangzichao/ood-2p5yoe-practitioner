rootProject.name = "ood-practice"

include(":common")

// Auto-discover exercise subprojects under exercises/* that contain a build.gradle.kts
file("exercises").listFiles { f -> f.isDirectory }?.forEach { dir ->
    val buildFile = java.io.File(dir, "build.gradle.kts")
    if (buildFile.exists()) {
        val path = ":exercises:${dir.name}"
        include(path)
        project(path).projectDir = dir
    }
}

