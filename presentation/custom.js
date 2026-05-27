window.addEventListener("DOMContentLoaded", () => {
  if (window.Reveal) {
    const updateTitleSlideState = () => {
      const currentSlide = window.Reveal.getCurrentSlide();
      const isTitleSlide =
        currentSlide?.id === "title-slide" ||
        currentSlide?.classList?.contains("title-slide");
      document.body.classList.toggle("on-title-slide", Boolean(isTitleSlide));
    };

    // Keep presenter state stable and allow CSS hooks post-initialization.
    window.Reveal.on("ready", () => {
      document.body.classList.add("slides-ready");
      updateTitleSlideState();
    });

    window.Reveal.on("slidechanged", (event) => {
      const section = event.currentSlide?.querySelector("h2");
      updateTitleSlideState();
      document.title = section
        ? `${section.textContent} | AfD Thesis Presentation`
        : "AfD Thesis Presentation";
    });
  }
});
