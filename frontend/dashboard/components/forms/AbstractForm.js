import React from "react";
import { useQueryClient } from "react-query";
import { Formik, Form } from "formik";
import { toast } from "react-toastify";
import Section from "./Section";
import DeleteButton from "./DeleteButton";
import UpdateButton from "./UpdateButton";
import TosurnamentApi from "../../api/TosurnamentApi";

export default function AbstractForm(props) {
  const { id, name, url, data, fields, invalidateQueryKeys, withDelete } = props;
  const queryClient = useQueryClient();

  let fieldsOfForm = [];
  for (const [fieldName, [fieldType, fieldProps]] of Object.entries(fields)) {
    fieldsOfForm.push(React.createElement(fieldType, { ...props, ...fieldProps, key: fieldName, fieldName }));
  }

  if (!data) {
    return <></>;
  }

  async function onSubmit(values, { setSubmitting, resetForm }) {
    try {
      await TosurnamentApi.put(url, values);
    } catch {
      return;
    } finally {
      setSubmitting(false);
    }
    resetForm({ values });
    toast.success("Update done");
    queryClient.invalidateQueries(invalidateQueryKeys);
  }

  async function onDeleteClick() {
    try {
      await TosurnamentApi.delete(url);
    } catch {
      return;
    }
    toast.success(`${name} deleted`);
    queryClient.invalidateQueries(invalidateQueryKeys);
  }

  function validate(values) {
    let errors = {};

    return errors;
  }

  return (
    <Section name={name} id={id}>
      <Formik initialValues={data} onSubmit={onSubmit}>
        {({ isSubmitting, isValid, dirty }) => (
          <Form>
            {fieldsOfForm}
            <UpdateButton isSubmitting={isSubmitting} disabled={!isValid || !dirty} />
            {withDelete ? <DeleteButton onClick={onDeleteClick} name={name} /> : null}
          </Form>
        )}
      </Formik>
    </Section>
  );
}
