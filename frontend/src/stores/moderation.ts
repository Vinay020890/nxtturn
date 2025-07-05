import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import type { AxiosError } from 'axios';

// Interface for the data we need to submit a report
interface ReportPayload {
  ct_id: number;
  obj_id: number;
  reason: string;
  details: string;
}

export const useModerationStore = defineStore('moderation', () => {
  // --- State ---
  const isSubmittingReport = ref(false);
  const submissionError = ref<string | null>(null);

  // --- Actions ---

  /**
   * Submits a new content report to the backend.
   * @param payload - The data for the report.
   * @returns boolean - True if submission was successful, false otherwise.
   */
  async function submitReport(payload: ReportPayload): Promise<boolean> {
    isSubmittingReport.value = true;
    submissionError.value = null;

    try {
      const url = `/content/${payload.ct_id}/${payload.obj_id}/report/`;
      
      // The backend expects 'reason' and 'details'
      const data = {
        reason: payload.reason,
        details: payload.details,
      };

      await axiosInstance.post(url, data);
      
      return true; // Report submission was successful

    } catch (error) {
      const axiosError = error as AxiosError<Record<string, any>>;
      if (axiosError.response?.data?.detail) {
        // Handle specific error messages from the backend like "You have already reported this content."
        submissionError.value = axiosError.response.data.detail;
      } else if (axiosError.response?.data) {
        // Handle other validation errors (e.g., details required for 'OTHER')
        submissionError.value = Object.values(axiosError.response.data).flat().join(' ');
      } else {
        submissionError.value = 'An unexpected error occurred while submitting the report.';
      }
      console.error("Report submission failed:", error);
      return false; // Report submission failed

    } finally {
      isSubmittingReport.value = false;
    }
  }

  return {
    isSubmittingReport,
    submissionError,
    submitReport,
  };
});